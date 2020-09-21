from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="brunt",
    version="0.1.3",
    author="Eduard van Valkenburg",
    author_email="eduardvanvalkenburg@outlook.com",
    description="Unofficial API for Brunt",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/eavanvalkenburg/brunt-api",
    classifiers=(
        'Development Status :: 3 - Alpha',
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
    packages=find_packages(),
    install_requires=['requests>=2.18.1'], 
)