SHELL := /bin/bash

init:
	python setup.py develop

test:
	nosetests -s tests

clean:
	git clean -Xfd
