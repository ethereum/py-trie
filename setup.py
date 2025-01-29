#!/usr/bin/env python
from setuptools import (
    find_packages,
    setup,
)

extras_require = {
    "dev": [
        "build>=0.9.0",
        "bump_my_version>=0.19.0",
        "eth-hash>=0.1.0,<1.0.0",
        "ipython",
        "pre-commit>=3.4.0",
        "tox>=4.0.0",
        "twine",
        "wheel",
    ],
    "docs": [
        "towncrier>=24,<25",
    ],
    "test": [
        "hypothesis>=6.56.4,<7",
        "pycryptodome",
        "pytest>=7.0.0",
        "pytest-xdist>=2.4.0",
    ],
}

extras_require["dev"] = (
    extras_require["dev"] + extras_require["docs"] + extras_require["test"]
)

with open("README.md") as readme_file:
    long_description = readme_file.read()

setup(
    name="trie",
    # *IMPORTANT*: Don't manually change the version here. Use the 'bump-my-version' utility.
    version="3.1.0",
    description="""Python implementation of the Ethereum Trie structure""",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="The Ethereum Foundation",
    author_email="snakecharmers@ethereum.org",
    url="https://github.com/ethereum/py-trie",
    include_package_data=True,
    install_requires=[
        "eth-hash>=0.1.0",
        "eth-utils>=2.0.0",
        "hexbytes>=0.2.3",
        "rlp>=3",
        "sortedcontainers>=2.1.0",
    ],
    python_requires=">=3.8, <4",
    extras_require=extras_require,
    py_modules=["trie"],
    license="MIT",
    zip_safe=False,
    keywords="ethereum blockchain evm trie merkle",
    packages=find_packages(exclude=["scripts", "scripts.*", "tests", "tests.*"]),
    package_data={"trie": ["py.typed"]},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
)
