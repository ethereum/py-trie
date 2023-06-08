#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages


extras_require = {
    "test": [
        "pytest>=7.0.0",
        "pytest-xdist>=2.4.0",
        "hypothesis>=6.56.4,<7",
        "pycryptodome",
    ],
    "lint": [
        "flake8==6.0.0",  # flake8 claims semver but adds new warnings at minor releases, leave it pinned.
        "flake8-bugbear==23.3.23",  # flake8-bugbear does not follow semver, leave it pinned.
        "isort>=5.10.1",
        "black>=23",
    ],
    "docs": [
        "towncrier>=21,<22",
    ],
    "dev": [
        "bumpversion>=0.5.3",
        "pytest-watch>=4.1.0",
        "tox>=4.0.0",
        "build>=0.9.0",
        "wheel",
        "twine",
        "eth-hash>=0.1.0,<1.0.0",
    ],
}

extras_require["dev"] = (
    extras_require["dev"]
    + extras_require["test"]
    + extras_require["lint"]
    + extras_require["docs"]
)

with open("README.md") as readme_file:
    long_description = readme_file.read()

setup(
    name="trie",
    # *IMPORTANT*: Don't manually change the version here. Use the 'bumpversion' utility.
    version="2.1.1",
    description="""Python implementation of the Ethereum Trie structure""",
    long_description_markdown_filename="README.md",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="The Ethereum Foundation",
    author_email="snakecharmers@ethereum.org",
    url="https://github.com/ethereum/py-trie",
    include_package_data=True,
    py_modules=["trie"],
    python_requires=">=3.7,<4",
    install_requires=[
        "eth-hash>=0.1.0",
        "eth-utils>=2.0.0",
        "hexbytes>=0.2.0",
        "rlp>=3",
        "sortedcontainers>=2.1.0",
        "typing-extensions>=4.0.0,<5; python_version < '3.8'",
    ],
    extras_require=extras_require,
    license="MIT",
    zip_safe=False,
    keywords="ethereum blockchain evm trie merkle",
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
