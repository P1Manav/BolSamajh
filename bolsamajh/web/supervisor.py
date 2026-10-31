"""BolSamajh Core Supervisor — Port fallback, runtime state, and health checking.

Provides:
- Automatic port fallback (tries 8000, then 8001..8020 if occupied)
- Single-instance detection with automatic dashboard activation
- Runtime metadata persistence (%LOCALAPPDATA%\\BolSamajh\\runtime.json)
- Rotating file logging (%LOCALAPPDATA%\\BolSamajh\\logs\\bolsamajh.log)
- Robust HTTP-based /healthz polling before opening any UI
"""

import json
import logging
import os
import socket
import time
import urllib.error
import urllib.request
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from bolsamajh import __version__

log = logging.getLogger("bolsamajh.supervisor")


def get_app_dir() -> Path:
    """Return application data directory: %LOCALAPPDATA%\\BolSamajh or ~/.bolsamajh."""
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        base = Path(local_app_data)
    else:
        base = Path.home() / ".local" / "share"
    app_dir = base / "BolSamajh"
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


def get_log_dir() -> Path:
    """Return logs directory: %LOCALAPPDATA%\\BolSamajh\\logs."""
    log_dir = get_app_dir() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def setup_rotating_file_logger(
    logger_name: str = "bolsamajh",
    max_bytes: int = 5 * 1024 * 1024,
    backup_count: int = 3,
) -> Path:
    """Add a rotating file handler to ensure logs are never lost in windowless mode."""
    log_file = get_log_dir() / "bolsamajh.log"
    root_log = logging.getLogger()

    # Avoid adding duplicate handlers
    for h in root_log.handlers:
        if isinstance(h, RotatingFileHandler) and getattr(h, "baseFilename", "") == str(log_file):
            return log_file

    try:
        handler = RotatingFileHandler(
            str(log_file),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        handler.setLevel(logging.INFO)
        root_log.addHandler(handler)
        log.info("Rotating file logging configured at %s", log_file)
    except Exception as e:
        log.warning("Could not setup file logger at %s: %s", log_file, e)

    return log_file


def is_port_in_use(host: str, port: int) -> bool:
    """Check if a network port is currently occupied."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        try:
            s.bind((host, port))
            return False
        except OSError:
            return True


def find_available_port(
    host: str = "127.0.0.1",
    start_port: int = 8000,
    max_tries: int = 25,
) -> int:
    """Find the first available port starting from start_port."""
    for p in range(start_port, start_port + max_tries):
        if not is_port_in_use(host, p):
            if p != start_port:
                log.info("Port %d was in use. Selected next available port %d", start_port, p)
            return p
    raise RuntimeError(
        f"Could not find an available port on {host} between {start_port} and {start_port + max_tries - 1}."
    )


def get_runtime_file() -> Path:
    """Return path to runtime.json."""
    return get_app_dir() / "runtime.json"


def write_runtime_info(host: str, port: int, log_file: Optional[Path] = None) -> Path:
    """Persist active runtime information to runtime.json."""
    runtime_file = get_runtime_file()
    payload = {
        "pid": os.getpid(),
        "host": host,
        "port": port,
        "version": __version__,
        "started_at": time.time(),
        "log_path": str(log_file or (get_log_dir() / "bolsamajh.log")),
    }
    try:
        temp_file = runtime_file.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        temp_file.replace(runtime_file)
        log.info("Wrote runtime info: %s:%d (PID %d)", host, port, os.getpid())
    except Exception as e:
        log.warning("Failed to write runtime.json: %s", e)
    return runtime_file


def read_runtime_info() -> Optional[Dict[str, Any]]:
    """Read existing runtime.json if present and valid."""
    runtime_file = get_runtime_file()
    if not runtime_file.is_file():
        return None
    try:
        with open(runtime_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def clean_runtime_info() -> None:
    """Remove runtime.json on application shutdown."""
    runtime_file = get_runtime_file()
    try:
        if runtime_file.exists():
            runtime_file.unlink()
    except Exception:
        pass


def check_health(host: str, port: int, timeout: float = 1.0) -> bool:
    """Probe /healthz endpoint. Returns True if server is healthy."""
    url = f"http://{host}:{port}/healthz"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "BolSamajh-Supervisor/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("status") == "ok" and data.get("app") == "BolSamajh"
    except Exception:
        return False
    return False


def wait_for_health(
    host: str,
    port: int,
    timeout: float = 15.0,
    check_interval: float = 0.15,
) -> bool:
    """Poll /healthz until healthy or timeout expires."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if check_health(host, port, timeout=0.5):
            return True
        time.sleep(check_interval)
    return False


def check_existing_instance() -> Optional[Tuple[str, int]]:
    """Check if another BolSamajh instance is already running and healthy.

    If running and healthy, returns (host, port). Otherwise returns None.
    """
    info = read_runtime_info()
    if not info:
        return None

    host = info.get("host", "127.0.0.1")
    port = info.get("port", 8000)

    if check_health(host, port, timeout=1.0):
        log.info("Found existing healthy BolSamajh instance running at http://%s:%d", host, port)
        return (host, port)

    return None

