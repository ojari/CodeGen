from setuptools import setup, find_packages

setup(
    name="py2code",
    version="0.1.1",
    description="A Python package for generating source code in C, C++, C#, and Java from python code.",
    author="Jari Ojanen",
    packages=find_packages(),
    install_requires=[],
    python_requires=">=3.9",
    url="https://github.com/ojari/codegen",
)