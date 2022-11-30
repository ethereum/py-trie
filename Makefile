CURRENT_SIGN_SETTING := $(shell git config commit.gpgSign)

.PHONY: clean-pyc clean-build docs

help:
	@echo "clean-build - remove build artifacts"
	@echo "clean-pyc - remove Python file artifacts"
	@echo "test - run tests quickly with the default Python"
	@echo "lint-roll - automatically fix problems with isort, flake8, etc"
	@echo "testall - run tests on every Python version with tox"
	@echo "coverage - check code coverage quickly with the default Python"
	@echo "docs - generate docs and open in browser (linux-docs for version on linux)"
	@echo "release - package and upload a release (does not run notes target)"
	@echo "dist - package"

clean: clean-build clean-pyc

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr *.egg-info

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -rf {} +

lint:
	tox -elint

lint-roll:
	isort <MODULE_NAME> tests
	black <MODULE_NAME> tests setup.py
	$(MAKE) lint

test:
	pytest --tb native tests

testall:
	tox

coverage:
	coverage run --source trie
	coverage report -m
	coverage html
	open htmlcov/index.html

docs:
	rm -f docs/trie.rst
	rm -f docs/modules.rst
	sphinx-apidoc -o docs/ -d 2 trie/
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	open docs/_build/html/index.html

check-bump:
ifndef bump
	$(error bump must be set, typically: major, minor, patch, or devnum)
endif

release: check-bump clean
	# require that you be on a branch that's linked to upstream/master
	git status -s -b | head -1 | grep "\.\.upstream/master"
	# verify that docs build correctly
	./newsfragments/validate_files.py is-empty
	make build-docs
	CURRENT_SIGN_SETTING=$(git config commit.gpgSign)
	git config commit.gpgSign true
	bumpversion $(bump)
	git push upstream && git push upstream --tags
	python setup.py sdist bdist_wheel
	twine upload dist/*
	git config commit.gpgSign "$(CURRENT_SIGN_SETTING)"

dist: clean
	python setup.py sdist bdist_wheel
	ls -l dist
