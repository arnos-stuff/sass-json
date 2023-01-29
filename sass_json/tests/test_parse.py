import json
from pathlib import Path

from ..io import rawparse, read_sass
from ..utils import console, PathLike


example_dir = Path(__file__).parent / "examples"
example_file = example_dir / "theme.scss"

console.print(example_file)

class TestParse:
    """Test that the parse function returns a dict"""
    def __new__(cls, file: PathLike = example_file, name: str = "raw"):
        cls.file = Path(file)
        cls.rawdict = rawparse(cls.file)
        cls.raw = open(file, "r").read()
        cls.sass = None
        cls.name = name

        if name != "raw":
            cls.sass = read_sass(cls.file)
        return cls

    @staticmethod
    def from_file(file: PathLike = example_file):
        class_instance = TestParse()
        class_instance.file = Path(file)
        class_instance.rawdict = rawparse(file)
        class_instance.raw = open(file, "r").read()
        return class_instance

    @classmethod
    def save_json(cls):
        rawname = f"raw-{cls.file.with_suffix('.json').name}"
        sassname = f"processed-{cls.file.with_suffix('.json').name}"
        with open(example_dir / rawname , "w+") as f:
            json.dump(cls.rawdict, f, indent=4)
        console.print(f"✅ Saved {rawname}", style="green")
        if cls.name != "raw":
            with open(example_dir / sassname , "w+") as f:
                json.dump(cls.sass, f, indent=4)
            console.print(f"✅ Saved {sassname}", style="green")

    @classmethod
    def show_raw(cls):
        console.print(cls.rawdict)
    
    @classmethod
    def show_sass(cls):
        console.print(cls.sass)

    @classmethod
    def show(cls, name: str):
        if name == "raw":
            cls.show_raw()
        elif name == "sass":
            cls.show_sass()
        else:
            console.print(f"❌ Invalid argument: {name}", style="red")