#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages


extras_require = {
    'test': [
        "pytest-xdist",
        "tox>=2.6.0,<3",
        "hypothesis==3.7.0",
        "pycryptodome",
    ],
    'lint': [
        "flake8==3.4.1",
    ],
    'dev': [
        "bumpversion>=0.5.3,<1",
        "wheel",
        "twine",
        "eth-hash>=0.1.0,<1.0.0",
    ],
}

extras_require['dev'] = (
    extras_require['dev'] +
    extras_require['test'] +
    extras_require['lint']
)

setup(
    name='trie',
    # *IMPORTANT*: Don't manually change the version here. Use the 'bumpversion' utility.
    version='1.4.0',
    description="""Python implementation of the Ethereum Trie structure""",
    long_description_markdown_filename='README.md',
    author='Piper Merriam',
    author_email='pipermerriam@gmail.com',
    url='https://github.com/ethereum/py-trie',
    include_package_data=True,
    py_modules=['trie'],
    setup_requires=['setuptools-markdown'],
    python_requires='>=3.5.3,<4',

    install_requires=[
        "eth-hash>=0.1.0,<1.0.0",
        "eth-utils>=1.3.0,<2.0.0",
        "rlp>=1,<2",
    ],
    extras_require=extras_require,
    license="MIT",
    zip_safe=False,
    keywords='ethereum blockchain evm trie merkle',
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        "Operating System :: OS Independent",
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development',
        'Topic :: Utilities',
    ],
)
