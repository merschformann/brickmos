import setuptools

# read the contents of README
from os import path

current_dir = path.abspath(path.dirname(__file__))
with open(path.join(current_dir, "README.md"), encoding="utf-8") as f:
    long_description = f.read()


setuptools.setup(
    name="brickmos",
    description="brickmos - A simple brick mosaic generator",
    long_description=long_description,
    long_description_content_type="text/markdown",
    version="0.0.3",
    author="Marius Merschformann",
    author_email="marius.merschformann@gmail.com",
    url="https://github.com/merschformann/brickmos",
    packages=setuptools.find_packages(),
    install_requires=[
        "opencv-python~=4.4.0.44",
    ],
    entry_points={
        "console_scripts": ["brickmos=brickmos.brickify:main"],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Environment :: Console",
    ],
)
