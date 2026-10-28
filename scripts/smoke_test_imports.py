"""BolSamajh — Import Smoke Test for Linux/Ubuntu and Cross-Platform CI.

Verifies that every module in the package can be successfully imported
even when optional hardware/GUI dependencies (such as tkinter, pystray,
keyboard, sounddevice) are unavailable or headless.
"""

import importlib
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("smoke_test")

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))


def get_all_bolsamajh_modules():
    """Discover all importable modules under the bolsamajh package."""
    modules = []
    package_dir = ROOT_DIR / "bolsamajh"
    for py_file in package_dir.rglob("*.py"):
        rel_path = py_file.relative_to(ROOT_DIR)
        parts = list(rel_path.parts)
        if parts[-1].endswith(".py"):
            parts[-1] = parts[-1][:-3]
        if parts[-1] == "__init__":
            parts = parts[:-1]
        mod_name = ".".join(parts)
        if mod_name and mod_name not in modules:
            modules.append(mod_name)
    return sorted(modules)


def run_smoke_test():
    all_modules = get_all_bolsamajh_modules()
    log.info("Discovered %d bolsamajh modules to smoke test", len(all_modules))

    failed = []
    passed = 0

    # Test 1: Direct imports
    for mod_name in all_modules:
        try:
            importlib.import_module(mod_name)
            passed += 1
            log.info("  ✓ %s", mod_name)
        except Exception as e:
            log.error("  ✗ Failed to import %s: %s", mod_name, e)
            failed.append((mod_name, str(e)))

    if failed:
        log.error("Import smoke test failed for %d modules!", len(failed))
        for m, err in failed:
            log.error("  - %s: %s", m, err)
        return 1

    # Test 2: Simulated missing optional dependencies (headless Linux / minimal env)
    log.info(
        "\nTesting imports with optional desktop/audio modules masked (headless simulation)..."
    )
    optional_modules = ["pystray", "keyboard", "tkinter"]
    original_modules = {}
    for opt in optional_modules:
        original_modules[opt] = sys.modules.get(opt)
        sys.modules[opt] = None  # Causes ImportError on attempt to import

    try:
        # Crucial cross-platform modules that must survive missing GUI/desktop hooks
        critical_modules = [
            "bolsamajh.config",
            "bolsamajh.prompts",
            "bolsamajh.overlay.hud",
            "bolsamajh.overlay.tray",
            "bolsamajh.web.server",
            "bolsamajh.documents.loader",
            "bolsamajh.documents.chunker",
            "bolsamajh.documents.retriever",
            "bolsamajh.pipeline.doc_qa",
            "bolsamajh.utils.text_cleanup",
            "bolsamajh.utils.sentence_splitter",
        ]
        for mod_name in critical_modules:
            if mod_name in sys.modules:
                del sys.modules[mod_name]
            importlib.import_module(mod_name)
            log.info("  ✓ (headless-safe) %s", mod_name)
    finally:
        # Restore sys.modules
        for opt, orig in original_modules.items():
            if orig is not None:
                sys.modules[opt] = orig
            else:
                sys.modules.pop(opt, None)

    log.info("\nImport smoke test PASSED: all %d modules loaded cleanly.", passed)
    return 0


if __name__ == "__main__":
    sys.exit(run_smoke_test())
