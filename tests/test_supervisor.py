"""Unit tests for BolSamajh Core Supervisor."""

import os
from pathlib import Path
import tempfile
from unittest.mock import patch

from bolsamajh.web.supervisor import (
    clean_runtime_info,
    find_available_port,
    get_app_dir,
    get_log_dir,
    get_runtime_file,
    is_port_in_use,
    read_runtime_info,
    setup_rotating_file_logger,
    write_runtime_info,
)


def test_supervisor_app_and_log_dir():
    app_dir = get_app_dir()
    assert app_dir.exists()
    assert "BolSamajh" in str(app_dir)

    log_dir = get_log_dir()
    assert log_dir.exists()
    assert log_dir.parent == app_dir


def test_find_available_port():
    port = find_available_port("127.0.0.1", start_port=8950, max_tries=5)
    assert 8950 <= port < 8955
    assert not is_port_in_use("127.0.0.1", port)


def test_runtime_info_lifecycle():
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_runtime = Path(tmpdir) / "runtime.json"
        with patch("bolsamajh.web.supervisor.get_runtime_file", return_value=fake_runtime):
            # Initially none
            assert read_runtime_info() is None

            # Write
            write_runtime_info("127.0.0.1", 8042)
            assert fake_runtime.exists()

            info = read_runtime_info()
            assert info is not None
            assert info["host"] == "127.0.0.1"
            assert info["port"] == 8042
            assert "pid" in info
            assert "version" in info

            # Clean
            clean_runtime_info()
            assert not fake_runtime.exists()
            assert read_runtime_info() is None


def test_setup_rotating_file_logger():
    log_file = setup_rotating_file_logger()
    assert log_file.name == "bolsamajh.log"
    assert log_file.parent.exists()

