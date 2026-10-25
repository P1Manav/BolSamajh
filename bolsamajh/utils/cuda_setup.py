"""CUDA DLL path configuration and auto-detection for Windows.

Adheres to Tier 3 Requirement 18:
- Discovers NVIDIA cuBLAS and cuDNN pip wheels dynamically (nvidia-cublas-cu12, nvidia-cudnn-cu12).
- Eliminates hardcoded vendor paths (e.g. ChatRTX).
- Automatically detects GPU vs CPU with int8 fallback and optimized model selection.
"""

import os
import sys
import logging
from pathlib import Path

log = logging.getLogger(__name__)

_CONFIGURED = False


def setup_cuda_dlls() -> bool:
    """Register CUDA DLL directories dynamically from Python site-packages and standard paths."""
    global _CONFIGURED
    if _CONFIGURED:
        return True

    if sys.platform != "win32":
        _CONFIGURED = True
        return True

    found_any = False

    # 1. Dynamically locate nvidia pip wheels (nvidia-cublas-cu12, nvidia-cudnn-cu12, etc.)
    site_packages_dirs = [p for p in sys.path if "site-packages" in p]
    for sp in site_packages_dirs:
        nvidia_root = Path(sp) / "nvidia"
        if nvidia_root.exists() and nvidia_root.is_dir():
            for subpkg in nvidia_root.iterdir():
                bin_dir = subpkg / "bin"
                if bin_dir.exists() and bin_dir.is_dir():
                    try:
                        os.add_dll_directory(str(bin_dir))
                        os.environ["PATH"] = str(bin_dir) + os.pathsep + os.environ.get("PATH", "")
                        found_any = True
                        log.debug("Registered nvidia wheel DLL directory: %s", bin_dir)
                    except Exception as e:
                        log.debug("Could not register DLL dir %s: %s", bin_dir, e)

    # 2. Check standard CUDA Toolkit paths if installed
    cuda_path = os.environ.get("CUDA_PATH")
    if cuda_path:
        cuda_bin = Path(cuda_path) / "bin"
        if cuda_bin.exists():
            try:
                os.add_dll_directory(str(cuda_bin))
                os.environ["PATH"] = str(cuda_bin) + os.pathsep + os.environ.get("PATH", "")
                found_any = True
                log.debug("Registered CUDA_PATH bin directory: %s", cuda_bin)
            except Exception as e:
                log.debug("Could not register CUDA_PATH dir %s: %s", cuda_bin, e)

    _CONFIGURED = True
    return found_any


def auto_detect_device() -> tuple[str, str, str]:
    """Auto-detect optimal compute device, compute type, and model.

    Returns:
        (device, compute_type, recommended_model)
        - On GPU: ('cuda', 'int8_float16', 'medium')
        - On CPU: ('cpu', 'int8', 'whisper-hinglish-swift')
    """
    setup_cuda_dlls()
    try:
        import ctranslate2
        cuda_count = ctranslate2.get_cuda_device_count()
        if cuda_count > 0:
            log.info("CUDA GPU detected (%d device(s)). Using cuda:int8_float16", cuda_count)
            return "cuda", "int8_float16", "medium"
    except Exception as e:
        log.debug("CUDA check exception: %s", e)

    log.info("No CUDA GPU detected or initialization failed. Falling back to CPU:int8 with swift model")
    return "cpu", "int8", "whisper-hinglish-swift"


# Auto-configure on module import
setup_cuda_dlls()
