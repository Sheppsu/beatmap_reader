from setuptools import setup, Extension


setup(
    ext_modules=[
        Extension(
            name="sliderpath",
            sources=["sliderpath.c"],
        ),
    ],
    zip_safe=False,
)
