#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages


setup(
    name='trie',
    # *IMPORTANT*: Don't manually change the version here. Use the 'bumpversion' utility.
    version='1.3.1',
    description="""Python implementation of the Ethereum Trie structure""",
    long_description_markdown_filename='README.md',
    author='Piper Merriam',
    author_email='pipermerriam@gmail.com',
    url='https://github.com/ethereum/py-trie',
    include_package_data=True,
    py_modules=['trie'],
    setup_requires=['setuptools-markdown'],
    install_requires=[
        "eth-utils>=1.0.0,<2.0.0",
        "rlp>=0.4.7,<1.0.0",
    ],
    license="MIT",
    zip_safe=False,
    keywords='ethereum blockchain evm trie merkle',
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
)
