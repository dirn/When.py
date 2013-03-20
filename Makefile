SHELL := /bin/bash

init:
	python setup.py develop

html:
	(cd docs && $(MAKE) html)

test:
	nosetests -s tests

clean:
	git clean -Xfd
