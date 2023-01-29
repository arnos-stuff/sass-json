import os
import re
import sys
import rich
import shutil
import subprocess
from pathlib import Path

from .utils import run_shell, console, run_shell_print_status as runshp

__all__ = ["npm_install", "git_install", "git_remove"]

def npm_install(package: str, silent: bool = False):
    """Install a package using npm"""
    None if silent else console.print(f"Installing {package} 🚀", style="bold green")
    runshp(f"npm install {package}")

def git_install(package_url: str, silent: bool = False):
    """Install a package using git clone & npm"""

    package = package_url.split("/")[-1].split(".")[0]

    None if silent else console.print(f"Installing {package} 🚀", style="bold green")
    runshp(f"git clone https://github.com/hakimel/reveal.js.git {package}")
    None if silent else console.print(
        f"✅ {package} installed successfully", style="bold green"
    )

    os.chdir(path=f"{package}")
    console.print("Installing dependencies 📦", style="bold green")
    os.system("npm install")
    None if silent else console.print(
        f"✅ {package} dependencies installed successfully", style="bold green"
    )
    os.chdir(path="..")

def remove_readonly(func, path, excinfo):
    if os.path.exists(path):
        os.chmod(path, 0o777)
        func(path)

def git_remove(
    dir: str,
    silent=False
    ):
    """Remove npm package installed in the target directory"""

    if os.path.isdir(dir):
        shutil.rmtree(dir, onerror=remove_readonly)
    else:
        None if silent else console.print(f"⚠️ {dir} not found", style="bold red")

    if not os.path.exists(dir):
        None if silent else console.print(
            f"✅ {dir} removed successfully", style="bold green"
        )
    else:
        None if silent else console.print(
            f"⚠️ {dir} not found", style="bold red"
        )