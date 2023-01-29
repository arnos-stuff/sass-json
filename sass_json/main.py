import os
import typer

from .utils import console, run_shell_print_status as runshp
from .installers import npm_install
from .meta import meta_install_pkgman

from .tests.test_parse import TestParse

app = typer.Typer(
    name="jsass",
    help="A simple CLI to convert JSON to SASS variables",
    add_completion=True,
    no_args_is_help=True,
)

@app.command(
    name="test",
    help="""Run tests 🧪 on the package.
    
    Currently, only the parsing of JSON is tested.
    """,
)
def test_parse(
    test_name: str = typer.Option(None, "-n", "--name",
        help="The name of the test to run. Defaults to 'parse'."
        ),
    save: bool = typer.Option(
        False, "-s", "--save", help="Save the test results to a file."
        ),
    ):
    """Test the parsing of JSON"""
    if not test_name:
        test_name = "raw"
    tester = TestParse(name = test_name)
    tester.save_json() if save else None
    tester.show(test_name)

@app.command(
    name="install",
    help="""Install a package using npm.
    
    Currently, the focus is on the installation of Dart Sass on Windows 10+.
    If you are on a different OS, we can still help you if you've installed
    either npm, yarn, apt, brew...
    """
)
def install(
    package: str = typer.Argument(..., help="The name of the package to install."),
    pkgman: str = typer.Option(None, help="The package manager to use."),
    ):
    """Install a package using npm"""
    if not pkgman:
        pkgman = "npm"
        if npm_install(package):
            return
    if not runshp(f"{pkgman} install {package}"):
        console.print(
            f"⚠️ Could not install {package} using {pkgman}",
            style="bold red"
            )
    meta_install_pkgman(os.platform)

if __name__ == "__main__":
    app()
    
    