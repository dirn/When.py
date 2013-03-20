SHELL := /bin/bash

init:
	python setup.py develop

publish:
	python setup.py sdist upload

html:
	(cd docs && $(MAKE) html)

test:
	nosetests -s tests

clean:
	git clean -Xfd
