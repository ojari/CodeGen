from setuptools import setup, find_packages

setup(
    name="py2code",
    version="0.2.0",
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