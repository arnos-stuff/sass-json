import os
import subprocess
from typing import Union
from pathlib import Path
from rich.console import Console

console = Console()

__all__ = ["run_shell", "run_shell_print_status", "PathLike"]

## types

PathLike = Union[str, Path, os.PathLike]

## functions

def run_shell(cmd: str):
    """Run a shell command"""
    return subprocess.run(
        cmd,
        shell=True,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
        )

def run_shell_print_status(
    cmd: str,
    console = console,
    success: str = "ran successfully",
    error: str = "could not be run"
    ):
    """Run a shell command and print the status"""
    response = run_shell(cmd)
    if response.returncode == 0:
        console.print(f"✅ {cmd} {success}", style="bold green")
    else:
        console.print(f"⚠️ {cmd} {error}", style="bold red")
        console.print(f"Error: {response.stderr.decode('utf-8')}", style="bold red", output=sys.stderr)
    return not response.returncode