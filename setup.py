from setuptools import setup, find_packages
import os
import re

# Path to the directory containing setup.py
HERE = os.path.abspath(os.path.dirname(__file__))

def get_version(rel_path):
    """Reads version from a file relative to HERE."""
    abs_path = os.path.join(HERE, rel_path)
    with open(abs_path, 'r') as f:
        for line in f: # Read line by line to avoid large file reads
            if line.startswith('__version__'):
                # Example: __version__ = "0.1.0"
                delim = '"' if '"' in line else "'"
                return line.split(delim)[1]
    raise RuntimeError("Unable to find version string.")

setup(
    name="autopr_cli",
    version=get_version("autopr/__init__.py"),
    py_modules=["run_cli"],
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "autopr=run_cli:main",
        ],
    },
    install_requires=[],
    author="Pedro Leao",
    author_email="leaop54@gmail.com",
    description="A CLI tool to automate PR creation and listing.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/leaopedro/autopr",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
