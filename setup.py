#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages


extras_require = {
    'test': [
        "pytest-xdist>=1.31.0,<2",
        "tox>=2.6.0,<3",
        "hypothesis>=5.10.4,<6",
        "pycryptodome",
    ],
    'lint': [
        "flake8==3.8.1",
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

with open('README.md') as readme_file:
    long_description = readme_file.read()

setup(
    name='trie',
    # *IMPORTANT*: Don't manually change the version here. Use the 'bumpversion' utility.
    version='2.0.0-alpha.4',
    description="""Python implementation of the Ethereum Trie structure""",
    long_description_markdown_filename='README.md',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='The Ethereum Foundation',
    author_email='snakecharmers@ethereum.org',
    url='https://github.com/ethereum/py-trie',
    include_package_data=True,
    py_modules=['trie'],
    python_requires='>=3.6,<4',

    install_requires=[
        "eth-hash>=0.1.0,<1.0.0",
        "eth-utils>=1.6.1,<2.0.0",
        "hexbytes>=0.2.0,<0.3.0",
        "rlp>=1,<=2.0.0-alpha.1",
        "sortedcontainers>=2.1.0,<3",
        "typing-extensions>=3.7.4,<4",
    ],
    extras_require=extras_require,
    license="MIT",
    zip_safe=False,
    keywords='ethereum blockchain evm trie merkle',
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        "Operating System :: OS Independent",
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Software Development',
        'Topic :: Utilities',
    ],
)
