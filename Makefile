SHELL := /bin/bash

init:
	python setup.py develop

test:
	nosetests ./tests/*

clean:
	git clean -Xfd
