"""Tests for libexec/agent_sep_sesam."""
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

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
