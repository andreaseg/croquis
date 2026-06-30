import PyInstaller.__main__
from pathlib import Path

HERE = Path(__file__).parent.absolute()
path_to_main = str(HERE / "croquis/main.py")


def build_executable():
    PyInstaller.__main__.run(
        [
            path_to_main,
            "--onefile",
            "--windowed",
            "--icon",
            "icon.ico",
            "-n",
            "croquis",
            "--add-data",
            "icon.ico:.",
        ]
    )


if __name__ == "__main__":
    build_executable()
