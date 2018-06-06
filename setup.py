import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="brunt",
    version="0.0.2",
    author="Eduard van Valkenburg",
    author_email="eduardvanvalkenburg@outlook.com",
    description="Unofficial API for Brunt",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/eavanvalkenburg/brunt-api",
    packages=setuptools.find_packages(),
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
    install_requires=['requests>=2.18.1'], 
)