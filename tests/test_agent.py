"""Tests for libexec/agent_sep_sesam."""
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import importlib.machinery
import importlib.util
import types

AGENT_PATH = Path(__file__).parent.parent / "local/lib/python3/cmk_addons/plugins/sep_sesam/libexec/agent_sep_sesam"


def load_agent():
    """Load agent_sep_sesam as a module (it has no .py extension)."""
    loader = importlib.machinery.SourceFileLoader("agent_sep_sesam", str(AGENT_PATH))
    spec = importlib.util.spec_from_loader("agent_sep_sesam", loader)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestFetchBackupjobs:
    def setup_method(self):
        self.agent = load_agent()
        self.client = MagicMock()

    def _make_tasks_response(self, tasks):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = tasks
        return resp

    def test_returns_tasks_from_each_group(self):
        self.client.get.return_value = self._make_tasks_response([
            {"name": "task_a", "resultsSts": "SUCCESSFUL", "exec": True},
            {"name": "task_b", "resultsSts": "WARNING", "exec": True},
        ])
        result = self.agent.fetch_backupjobs(self.client, ["grp1"])
        assert len(result) == 2
        assert result[0]["name"] == "task_a"
        assert result[0]["resultsSts"] == "SUCCESSFUL"
        assert result[0]["group"] == "grp1"

    def test_calls_correct_endpoint(self):
        self.client.get.return_value = self._make_tasks_response([])
        self.agent.fetch_backupjobs(self.client, ["my_group"])
        self.client.get.assert_called_once_with("/backupgroups/my_group/tasks")

    def test_multiple_groups_merged(self):
        self.client.get.side_effect = [
            self._make_tasks_response([{"name": "t1", "resultsSts": "SUCCESSFUL", "exec": True}]),
            self._make_tasks_response([{"name": "t2", "resultsSts": "ERROR", "exec": True}]),
        ]
        result = self.agent.fetch_backupjobs(self.client, ["g1", "g2"])
        assert len(result) == 2
        assert result[0]["group"] == "g1"
        assert result[1]["group"] == "g2"

    def test_http_error_sets_error_field(self):
        resp = MagicMock()
        resp.status_code = 500
        self.client.get.return_value = resp
        result = self.agent.fetch_backupjobs(self.client, ["grp1"])
        assert result[0]["error"] == "HTTP 500"

    def test_empty_groups_returns_empty(self):
        result = self.agent.fetch_backupjobs(self.client, [])
        assert result == []
        self.client.get.assert_not_called()

    def test_disabled_task_still_included(self):
        self.client.get.return_value = self._make_tasks_response([
            {"name": "disabled_task", "resultsSts": "SUCCESSFUL", "exec": False},
        ])
        result = self.agent.fetch_backupjobs(self.client, ["grp1"])
        assert len(result) == 1
        assert result[0]["exec"] is False


class TestFetchLicenseEnhanced:
    def setup_method(self):
        self.agent = load_agent()
        self.client = MagicMock()

    SAMPLE_LICENSE_RESPONSE = [
        "2020-09-09 15:15:04: sm_info c",
        "License: ok  ",
        "Edition: Ultimate Volume",
        "Customer        : SEP-AG",
        "Customer No.    : 12345",
        "Issued          : 2019-07-04 09:29:14",
        "Service Modality: Maintenance",
        "Time  : Date of Installation 201805220847  lasting unlimited days",
        "      : Maintenance expiration date 2099-12-31",
        "Volume Based License:",
        "   1.023 TB of 21  TB FrontSide",
    ]

    def _make_response(self, lines, status=200):
        resp = MagicMock()
        resp.status_code = status
        resp.json.return_value = lines
        resp.text = "\n".join(lines)
        return resp

    def test_parses_edition(self):
        self.client.post.return_value = self._make_response(self.SAMPLE_LICENSE_RESPONSE)
        result = self.agent.fetch_license(self.client)
        assert result["edition"] == "Ultimate Volume"

    def test_parses_customer(self):
        self.client.post.return_value = self._make_response(self.SAMPLE_LICENSE_RESPONSE)
        result = self.agent.fetch_license(self.client)
        assert result["customer"] == "SEP-AG"

    def test_parses_volume_used(self):
        self.client.post.return_value = self._make_response(self.SAMPLE_LICENSE_RESPONSE)
        result = self.agent.fetch_license(self.client)
        assert result["volume_used_tb"] == pytest.approx(1.023, abs=0.001)
        assert result["volume_total_tb"] == 21.0

    def test_missing_edition_is_none(self):
        lines = ["License: ok", "      : Maintenance expiration date 2099-12-31"]
        self.client.post.return_value = self._make_response(lines)
        result = self.agent.fetch_license(self.client)
        assert result["edition"] is None

    def test_missing_volume_returns_none(self):
        lines = ["License: ok", "      : Maintenance expiration date 2099-12-31"]
        self.client.post.return_value = self._make_response(lines)
        result = self.agent.fetch_license(self.client)
        assert result["volume_used_tb"] is None
        assert result["volume_total_tb"] is None

    def test_existing_expiry_still_works(self):
        self.client.post.return_value = self._make_response(self.SAMPLE_LICENSE_RESPONSE)
        result = self.agent.fetch_license(self.client)
        assert result["expiration_date"] == "2099-12-31"
        assert result["days_remaining"] > 0


class TestFetchServerInfo:
    def setup_method(self):
        self.agent = load_agent()
        self.client = MagicMock()

    SAMPLE_SERVER_INFO = {
        "name": "sesam-server",
        "release": "5.2.0.3",
        "kernel": "5.2.0",
        "os": "Linux",
        "dbType": "postgres",
        "javaVersion": "11.0.12",
        "timezone": "Europe/Berlin",
    }

    def _make_response(self, data, status=200):
        resp = MagicMock()
        resp.status_code = status
        resp.json.return_value = data
        return resp

    def test_calls_server_info_endpoint(self):
        self.client.get.return_value = self._make_response(self.SAMPLE_SERVER_INFO)
        self.agent.fetch_server_info(self.client)
        self.client.get.assert_called_once_with("/server/info")

    def test_returns_key_fields(self):
        self.client.get.return_value = self._make_response(self.SAMPLE_SERVER_INFO)
        result = self.agent.fetch_server_info(self.client)
        assert result["release"] == "5.2.0.3"
        assert result["os"] == "Linux"
        assert result["dbType"] == "postgres"
        assert result["javaVersion"] == "11.0.12"
        assert result["timezone"] == "Europe/Berlin"
        assert result["error"] is None

    def test_http_error_sets_error(self):
        self.client.get.return_value = self._make_response({}, status=401)
        result = self.agent.fetch_server_info(self.client)
        assert result["error"] == "HTTP 401"

    def test_request_exception_sets_error(self):
        import requests
        self.client.get.side_effect = requests.RequestException("timeout")
        result = self.agent.fetch_server_info(self.client)
        assert "timeout" in result["error"]
