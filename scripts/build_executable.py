"""Build a standalone Windows executable release package for BolSamajh using PyInstaller.

Produces:
  dist/BolSamajh/BolSamajh.exe
  dist/BolSamajh-v<version>-windows-x64.zip
"""

import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


def build_app(enable_console: bool = False, package_only: bool = False):
    root = Path(__file__).resolve().parent.parent
    os.chdir(root)

    print("=================================================================")
    print("  BolSamajh -- Standalone Release Executable Builder")
    print("=================================================================")

    # 1. Ensure icon is generated
    ico_path = root / "assets" / "bolsamajh.ico"
    if not ico_path.exists():
        print("[*] Generating application icon...")
        from scripts.generate_icon import generate_icon

        generate_icon()

    # 2. Check or install PyInstaller in environment
    try:
        import importlib.util

        if importlib.util.find_spec("PyInstaller") is None:
            raise ImportError
    except ImportError:
        print("[*] Installing PyInstaller into current environment...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # 3. Read version
    version = "1.1.0"
    try:
        import bolsamajh

        version = getattr(bolsamajh, "__version__", version)
    except Exception:
        pass

    dist_dir = root / "dist"
    app_output_dir = dist_dir / "BolSamajh"

    if not package_only:
        # Clean previous build artifacts
        if app_output_dir.exists():
            print(f"[*] Cleaning previous build at {app_output_dir}...")
            shutil.rmtree(app_output_dir, ignore_errors=True)

        # 4. Construct PyInstaller command line
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name=BolSamajh",
        "--onedir",
        f"--icon={ico_path}",
        "--clean",
        "--noconfirm",
    ]

    if enable_console:
        cmd.append("--console")
    else:
        cmd.append("--noconsole")

    # Add data directories
    static_src = root / "bolsamajh" / "web" / "static"
    if static_src.exists():
        cmd.extend(["--add-data", f"{static_src}{os.pathsep}bolsamajh/web/static"])

    assets_src = root / "assets"
    if assets_src.exists():
        cmd.extend(["--add-data", f"{assets_src}{os.pathsep}assets"])

    models_piper = root / "models" / "piper"
    if models_piper.exists():
        cmd.extend(["--add-data", f"{models_piper}{os.pathsep}models/piper"])

    calib_json = root / "benchmark_data" / "calibrated_thresholds.json"
    if calib_json.exists():
        cmd.extend(["--add-data", f"{calib_json}{os.pathsep}benchmark_data"])

    # Add hidden imports
    hidden_imports = [
        "bolsamajh",
        "bolsamajh.main",
        "bolsamajh.overlay.hud",
        "bolsamajh.overlay.tray",
        "bolsamajh.web.server",
        "bolsamajh.pipeline.dictation",
        "bolsamajh.pipeline.doc_qa",
        "bolsamajh.pipeline.commands",
        "bolsamajh.stt.faster_whisper_stt",
        "bolsamajh.tts.edge_tts_adapter",
        "bolsamajh.tts.piper_adapter",
        "bolsamajh.llm.ollama_adapter",
        "bolsamajh.llm.google_ai",
        "bolsamajh.documents.loader",
        "bolsamajh.documents.retriever",
        "bolsamajh.documents.chunker",
        "bolsamajh.utils.audio",
        "bolsamajh.utils.clipboard",
        "bolsamajh.utils.vad",
        "bolsamajh.utils.sentence_splitter",
        "bolsamajh.utils.text_cleanup",
        "bolsamajh.utils.cuda_setup",
        "uvicorn",
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "fastapi",
        "fastapi.staticfiles",
        "pystray",
        "PIL",
        "PIL.Image",
        "pynput",
        "keyboard",
        "pyperclip",
        "sounddevice",
        "soundfile",
        "aksharamukha",
        "aksharamukha.transliterate",
        "fitz",
        "docx",
        "trafilatura",
        "silero_vad",
        "edge_tts",
        "ctranslate2",
        "faster_whisper",
        "av",
        "av.audio",
        "av.audio.resampler",
        "sentence_transformers",
        "transformers",
        "torch",
        "faiss",
    ]

    for hi in hidden_imports:
        cmd.extend(["--hidden-import", hi])

    # Collect all modules and packages from packages that dynamic import
    collect_packages = [
        "ctranslate2",
        "faster_whisper",
        "sounddevice",
        "soundfile",
        "pystray",
        "av",
        "faiss",
    ]
    for pkg in collect_packages:
        cmd.extend(["--collect-all", pkg])

    # Entry point script
    entry_point = root / "bolsamajh" / "__main__.py"
    cmd.append(str(entry_point))

    if not package_only:
        print("[*] Compiling standalone application executable with PyInstaller...")
        print(f"    Command: {' '.join(cmd[:10])} ...")
        subprocess.check_call(cmd)

    exe_file = app_output_dir / "BolSamajh.exe"
    if not exe_file.exists():
        raise RuntimeError(f"Build failed: {exe_file} not found.")

    print(f"[OK] Executable built successfully: {exe_file}")

    # Copy launcher scripts and documentation into the distribution folder
    shutil.copy2(root / "README.md", app_output_dir / "README.md")
    shutil.copy2(root / "LICENSE", app_output_dir / "LICENSE")
    if (root / "Install-BolSamajh.bat").exists():
        shutil.copy2(root / "Install-BolSamajh.bat", app_output_dir / "Install-BolSamajh.bat")
    if (root / ".env.example").exists():
        shutil.copy2(root / ".env.example", app_output_dir / ".env.example")

    # 5. Create distributable zip archive
    zip_filename = f"BolSamajh-v{version}-windows-x64.zip"
    zip_path = dist_dir / zip_filename
    print(f"[*] Packaging into distribution archive: {zip_path}...")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file in app_output_dir.rglob("*"):
            arcname = file.relative_to(dist_dir)
            zipf.write(file, arcname)

    size_mb = zip_path.stat().st_size / (1024 * 1024)
    print("[OK] Distribution package created successfully!")
    print(f"    Package: {zip_path} ({size_mb:.1f} MB)")
    print("=================================================================")
    print("  To use the app directly:")
    print(f"  1. Double-click: {exe_file}")
    print(f"  Or unzip {zip_filename} on any Windows machine!")
    print("=================================================================")
    return zip_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build BolSamajh Standalone Windows Executable")
    parser.add_argument(
        "--console",
        action="store_true",
        help="Build with visible console window (useful for debugging)",
    )
    parser.add_argument(
        "--package-only",
        action="store_true",
        help="Skip PyInstaller compilation and package existing dist/BolSamajh into zip",
    )
    args = parser.parse_args()

    build_app(enable_console=args.console, package_only=args.package_only)
