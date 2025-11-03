from setuptools import setup, find_packages
import os

def read_version():
    version_file = os.path.join(os.path.dirname(__file__), "py2code", "__init__.py")
    with open(version_file, "r") as f:
        for line in f:
            if line.startswith("__version__"):
                delim = '"' if '"' in line else "'"
                return line.split(delim)[1]
    raise RuntimeError("Unable to find version string.")

setup(
    name="py2code",
    version=read_version(),
    description="A Python package for generating source code in C, C++, C#, and Java from python code.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Jari Ojanen",
    packages=find_packages(),
    install_requires=[],
    python_requires=">=3.9",
    url="https://github.com/ojari/codegen",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Intended Audience :: Developers",
        "Topic :: Software Development",
        "Topic :: Software Development :: Code Generators"
    ]
)
