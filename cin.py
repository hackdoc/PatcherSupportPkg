"""
Postprocess binaries on CI
"""

# TODO: We need a proper way to identify and sign bundles. Unfortunately Apple does not make this easy.

import subprocess
import sys
from pathlib import Path

# Configurable options

IDENTITY = "hackdoc"
TARGET_DIR = Path("Universal-Binaries")
UNUSED = [
    # Mojave and Catalina non-Metal Patches
    # No longer used by us, but nice for reference
    "10.13.6-18",
    "10.13.6-19",
    "10.14.4-18",
    "10.14.4-19",
    "10.14.6-19",
    # Nvidia Web Driver Patches
    # Remove .pkg, unused by patcher
    "WebDriver-387.10.10.10.40.140/WebDriver-387.10.10.10.40.140.pkg",
    "WebDriver-387.10.10.10.40.140/WebDriver-387.10.10.15.15.108.pkg",
]

# Constants

MACHO_MAGIC = {
    "MH_MAGIC": b"\xfe\xed\xfa\xce",
    "MH_CIGAM": b"\xce\xfa\xed\xfe",
    "MH_MAGIC_64": b"\xfe\xed\xfa\xcf",
    "MH_CIGAM_64": b"\xcf\xfa\xed\xfe",
    "FAT_MAGIC": b"\xbe\xba\xfe\xca",
    "FAT_CIGAM": b"\xca\xfe\xba\xbe",
}


def clean_unused():
    """
    Remove unused files and folders
    """

    for path in UNUSED:
        path = TARGET_DIR / path
        if path.exists():
            print(f"Removing: {path}")
            subprocess.check_output(["rm", "-rf", path])

    for path in TARGET_DIR.rglob(".DS_Store"):
        print(f"Removing: {path}")
        path.unlink()


def get_machos(directory=TARGET_DIR):
    """
    Get all machos in a directory
    """

    machos: dict[Path, bytes] = {}
    for file in directory.rglob("*"):
        if not file.is_file() or file.is_symlink():
            continue
        with file.open("rb") as f:
            magic = f.read(4)
            if magic in MACHO_MAGIC.values():
                machos[file] = magic
    return dict(sorted(machos.items(), key=lambda item: item[0]))


def thin_macho(file: Path, magic: bytes):
    """
    Run lipo to thin a fat macho
    """

    if magic in (MACHO_MAGIC["FAT_MAGIC"], MACHO_MAGIC["FAT_CIGAM"]):
        subprocess.check_output(["lipo", "-thin", "x86_64", "-output", file, file])


if __name__ == "__main__":
    clean_unused()
    machos = get_machos()
    if not machos:
        print("No machos found!")
        sys.exit(1)
    for macho, magic in machos.items():
        thin_macho(macho, magic)
    print("Done!")
