"""F1: 프로젝트 뼈대 확인."""
import importlib
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_package_imports():
    pkg = importlib.import_module("asciiart")
    assert pkg.__version__


def test_required_libraries_available():
    for name in ("numpy", "PIL", "cv2"):
        importlib.import_module(name)


def test_no_web_leftovers():
    for name in ("package.json", "vite.config.ts", "tsconfig.json", "index.html", "src", "node_modules"):
        assert not (ROOT / name).exists(), name


def test_image_tool_present():
    assert (ROOT / "tools" / "image_to_field.py").is_file()
