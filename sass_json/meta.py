import os
import sys
import shutil

from time import sleep
from pathlib import Path
from rich.console import Console

from .utils import run_shell, console, run_shell_print_status as runshp

__all__ = [
    "find_package_manager",
    "meta_install_pkgman"
    ]

package_managers = {
    "windows": [
        "scoop",
        "choco",
        "brew"
    ],
    "linux": [
        "apt",
        "pacman",
        "yum",
        "dnf",
        "zypper",
        "apk"
    ],
    "darwin": [
        "brew",
        "port"
    ]
}

SASS_ERROR_MSG = """
⚠️ Sass could not be installed.
You will need to install it manually.
Here are some resources to help you:

If you are on Windows:
- https://scoop.sh/
- https://chocolatey.org/
- https://sass-lang.com/install
- https://www.npmjs.com/package/sass

If you are on Linux:
- https://stackoverflow.com/questions/39981828/installing-nodejs-and-npm-on-linux
- https://sass-lang.com/install
- https://www.npmjs.com/package/sass

If you are on MacOS:
- https://brew.sh/
- https://sass-lang.com/install
"""

fmt_pkgman = lambda opsys: "\n - " + "\n - ".join(package_managers[opsys])
fmt_platforms = "\n - " + "\n - ".join(package_managers.keys())


package_managers["win32"] = package_managers["windows"]


def find_package_manager(
    exit_if_error: bool = False,
    return_any: bool = True
    ) -> str:
    """Find the package manager"""
    if sys.platform not in package_managers:
        rich.print(
            (
                "⚠️ OS not supported !\n" +
                "This package only supports the following platforms:\n" +
                f"{fmt_platforms}"
            ),
            style="bold red"
            )
    else:
        pkgmans = [
            pkgman
            for pkgman in package_managers[sys.platform]
            if shutil.which(pkgman)
        ]
        if len(pkgmans):
            return pkgmans[0] if return_any else pkgmans
        rich.print(
            (
                "⚠️ Package manager not found\n" +
                "On your OS ({sys.platform}), this package\n" +
                "only supports the following package managers:\n" +
                f"{fmt_pkgman(sys.platform)}"
            ),
            style="bold red"
            )
    if exit_if_error:
        raise OSError("Package manager not found")
    return None

def meta_install_pkgman(package: str = "npm"):
    """Guesses the package manager your OS has and installs npm"""
    opsys = sys.platform
    console.print(
        "Attempting to find a pre-existing package 📦 manager 🔎",
        style="bold blue",
    )
    pkgman = find_package_manager()
    if pkgman:
        console.print(f"Found package manager: {pkgman} 🎉", style="bold green")
        console.print(f"Installing npm 🚀", style="bold green")
        if runshp(f"{pkgman} install npm", success="npm installed successfully"):
            return True
    else:
        console.print(f"No package manager found. Attempting to install one 🚀", style="bold blue")
        if opsys in ["windows", "win32"]:
            return windows_meta_install(package)
        elif opsys == "darwin":
            return macos_meta_install(package)
        elif opsys == "linux":
            return linux_meta_install(package)
        else:
            console.print(f"⚠️ OS not supported !", style="bold red")
            console.print(f"This package only supports the following platforms:\n{fmt_platforms}", style="bold red")
            raise OSError("OS not supported")


def windows_meta_install(package: str = "npm"):
    """Installs npm on windows using scoop"""
    if shutil.which(package):
        console.print(f"{package} already installed 🎉", style="bold green")
        return True
    elif shutil.which("scoop"):
        console.print("scoop already installed 🎉", style="bold green")
    else:
        console.print(f"Installing scoop 🚀", style="bold green")
        runshp(
            cmd="Set-ExecutionPolicy RemoteSigned -Scope CurrentUser",
            success="Execution policy set to RemoteSigned",
            error="Failed to set execution policy"
            )
        scoop_ok = runshp(
            cmd="irm get.scoop.sh | iex",
            success="Scoop installed successfully 🎉",
            error="Failed to install scoop"
            )
        if not scoop_ok:
            raise OSError("Failed to install scoop")

    if package in {"npm", "sass"}:
        console.print("Installing npm 🚀", style="bold green")
        if not runshp("scoop install npm", success="npm installed successfully"):
            raise OSError("Failed to install npm, but scoop is installed")
        if package != "sass":
            return True
        console.print("Installing sass 🚀", style="bold green")
        sass_ok = runshp(
            cmd="npm install -g sass",
            success="sass installed successfully 🎉",
            error="Failed to install sass"
            )
        if not sass_ok:
            raise OSError("Failed to install sass, but npm & scoop installed")
    return True


def macos_meta_install(package: str = "npm"):
    raise NotImplementedError("macOS not supported yet")

def linux_meta_install(package: str = "npm"):
    raise NotImplementedError("Linux not supported yet")

def meta_install_sass():
    """Guesses the package manager your OS has and installs sass"""
    if shutil.which("sass"):
        console.print("sass already installed 🎉", style="bold green")
        return True
    opsys = sys.platform
    console.print(f"Attempting to find a pre-existing package 📦 manager 🔎", style="bold blue")
    pkgmans = find_package_manager(return_any=False)
    if not len(pkgmans):
        console.print("No package managers found", style="bold red")
        if opsys in ["windows", "win32", "darwin"]:
            console.print("[bold red]Package manager not found[/bold red]")
            console.print("[bold magenta]However we will try to install one.[/bold red]")
            if opsys in ["windows", "win32"]:
                console.print("""
                [bold magenta]On Windows 2 options:[/bold magenta]
                - [bold blue]scoop[/bold blue] ==> npm ==> sass [bold green](recommended)[/bold green]
                - [bold blue]choco[/bold blue] ==> npm ==> sass [bold orange](not yet supported)[/bold red]
                """)
                sleep(1)
                console.print("[bold magenta]Installing scoop[/bold magenta]")
                windows_meta_install("sass")

            elif opsys == "darwin":
                console.print("""
                [bold magenta]On macOS 2 options:[/bold magenta]
                - [bold blue]brew[/bold blue] ==> npm ==> sass [bold orange](not yet supported)[/bold red]
                - [bold blue]macports[/bold blue] ==> npm ==> sass [bold orange](not yet supported)[/bold red]
                """)
                sleep(1)
                console.print("[bold magenta]Installing brew[/bold magenta]")
                macos_meta_install("sass")
        elif opsys == "linux":
            console.print("""
            [bold magenta]On Linux, this should have detected a package manager.[/bold magenta]
            
            What kind of far-fetched distro are you using that doesn't have a package manager? 🤔
            
            """)
            raise OSError("No package manager found")
    elif len(pkgmans) == 1:
        pkgman = pkgmans[0]
        console.print(f"Found package manager: {pkgman} 🎉", style="bold green")
        console.print(f"Installing sass 🚀", style="bold green")
        if not runshp(f"{pkgman} install sass", success="sass installed successfully"):
            console.print(f"Failed to install sass with {pkgman}", style="bold red")
            console.print(f"Attempting to install with npm", style="bold blue")

        if shutil.which("npm"):
            if not runshp("npm install -g sass", success="sass installed successfully"):
                console.print(f"Failed to install sass with npm", style="bold red")
                raise OSError("Failed to install sass")
        else:
            console.print(f"Installing npm 🚀", style="bold green")
            if not runshp(f"{pkgman} install npm", success="npm installed successfully"):
                console.print(f"Failed to install npm with {pkgman}", style="bold red")
                raise OSError("Failed to install npm")
            if not runshp("npm install -g sass", success="sass installed successfully"):
                console.print(f"Failed to install sass with npm", style="bold red")
                raise OSError("Failed to install sass, but npm installed")
    else:
        console.print(f"Installing sass 🚀", style="bold green")
        preferred_pkgman = (
            "scoop" if opsys in ["windows", "win32"] else "brew" if opsys == "darwin" else "apt"
        )
        if not shutil.which(preferred_pkgman):
            console.print(f"Did not find preferred package manager, Installing {preferred_pkgman} 🚀", style="bold green")
            preferred_pkgman = pkgmans[0]
            if opsys in ["windows", "win32"]:
                windows_meta_install("sass")
            elif opsys == "darwin":
                macos_meta_install("sass")
            elif opsys == "linux":
                linux_meta_install("sass")


    if pkgman:
        console.print(f"Found package manager: {pkgman} 🎉", style="bold green")
        console.print(f"Installing sass 🚀", style="bold green")
        if not runshp(f"{pkgman} install sass", success="sass installed successfully"):
            sys.exit(1)