import setuptools
import re

requirements = [
    "numpy>=1.22.4",
    "pygame>=2.1.2",
]  # Fallback

try:
    with open("beatmap_reader/requires.txt", 'r') as f:
        requirements = f.readlines()
except FileNotFoundError:
    try:
        with open("requirements.txt", 'r') as f:
            requirements = f.readlines()
    except FileNotFoundError:
        pass

readme = ''
with open('README.rst') as f:
    readme = f.read()

version = ''
with open('beatmap_reader/__init__.py') as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)

project_urls = {
    "Bug Tracker": "https://github.com/Sheepposu/beatmap_reader/issues",
}
classifiers = [
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
]

packages = [
    'beatmap_reader',
]

setuptools.setup(
    name="beatmap_reader",
    version=version,
    packages=packages,
    author="Sheepposu",
    description="Library for easily reading beatmaps",
    long_description=readme,
    long_description_content_type="text/plain",
    install_requires=requirements,
    project_urls=project_urls,
    classifiers=classifiers,
    python_requires=">=3.8.0",
    license="MIT",
    url="https://github.com/Sheepposu/beatmap_reader",
)
