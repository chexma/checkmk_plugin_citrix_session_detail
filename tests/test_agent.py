"""Tests for libexec/agent_sep_sesam."""
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import importlib.util
import types

AGENT_PATH = Path(__file__).parent.parent / "local/lib/python3/cmk_addons/plugins/sep_sesam/libexec/agent_sep_sesam"


def load_agent():
    """Load agent_sep_sesam as a module (it has no .py extension)."""
    spec = importlib.util.spec_from_file_location("agent_sep_sesam", AGENT_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
