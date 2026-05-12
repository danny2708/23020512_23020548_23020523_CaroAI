from pathlib import Path

from setuptools import Extension, setup

try:
    from Cython.Build import cythonize
except ImportError as exc:
    raise SystemExit(
        "Cython is required to build the acceleration module. "
        "Install build dependencies with: py -m pip install -r requirements.txt"
    ) from exc


ROOT = Path(__file__).resolve().parent
SOURCE_DIR = ROOT / "source_code"

extensions = [
    Extension(
        "accel.caro_accel",
        [str(SOURCE_DIR / "accel" / "caro_accel.pyx")],
    )
]

setup(
    name="caro-ai-accel",
    package_dir={"": "source_code"},
    ext_modules=cythonize(
        extensions,
        compiler_directives={
            "language_level": "3",
            "boundscheck": False,
            "wraparound": False,
            "initializedcheck": False,
            "cdivision": True,
        },
    ),
    zip_safe=False,
)
