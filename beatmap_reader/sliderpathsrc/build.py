from setuptools import setup, Extension
from pathlib import Path


working_dir = str(Path(__file__).parent.resolve())


setup(
    ext_modules=[
        Extension(
            name="sliderpath",
            sources=["sliderpath.c", "circulararc.c", "list.c", "vector.c"],
            define_macros=[("__FILE_OFFSET__", str(len(working_dir)))]
        ),
    ],
    zip_safe=False,
)
