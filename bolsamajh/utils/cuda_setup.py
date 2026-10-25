"""CUDA DLL path configuration for Windows.

Locates NVIDIA CUDA/cuBLAS/cuDNN runtime DLLs on Windows and registers
them via os.add_dll_directory and PATH so that CTranslate2 and PyTorch
find cublas64_12.dll and cudnn64_8.dll on GPU systems like RTX 3060 Ti.
"""

import os
import sys
import logging

log = logging.getLogger(__name__)

_CONFIGURED = False


def setup_cuda_dlls() -> bool:
    """Register CUDA DLL directories on Windows. Returns True if any found."""
    global _CONFIGURED
    if _CONFIGURED:
        return True

    if sys.platform != "win32":
        _CONFIGURED = True
        return True

    candidates = [
        r"C:\Program Files\NVIDIA Corporation\ChatRTX\env_nvd_rag\Lib\site-packages\torch\lib",
        r"C:\Program Files\NVIDIA Corporation\ChatRTX\env_nvd_rag\Lib\site-packages\nvidia\cublas\bin",
        r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4\bin",
        r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.2\bin",
        r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.0\bin",
    ]

    found_any = False
    for path_str in candidates:
        if os.path.isdir(path_str):
            try:
                os.add_dll_directory(path_str)
                os.environ["PATH"] = path_str + os.pathsep + os.environ.get("PATH", "")
                found_any = True
                log.debug("Registered CUDA DLL directory: %s", path_str)
            except Exception as e:
                log.debug("Could not register DLL dir %s: %s", path_str, e)

    _CONFIGURED = True
    return found_any


# Auto-configure on module import
setup_cuda_dlls()
