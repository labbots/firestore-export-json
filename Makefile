.PHONY: help venv clean run install
SHELL=/bin/bash

VENV_NAME?=venv
VENV_BIN=$(shell pwd)/${VENV_NAME}/bin

PYTHON=${VENV_BIN}/python

.DEFAULT: help

help:
	@echo "make install"
	@echo "    Installs package in your system."
	@echo "make clean"
	@echo "    Remove python artifacts and virtualenv."

venv: $(VENV_NAME)/bin/activate
$(VENV_NAME)/bin/activate: setup.py
	test -d $(VENV_NAME) || python -m venv $(VENV_NAME)
	touch $(VENV_NAME)/bin/activate
	${PYTHON} -m pip install -U pip setuptools
	${PYTHON} -m pip install -e .

clean:
	pip uninstall -y fs-to-json
	find . \( -name \*.pyc -o -name \*.pyo -o -name *~ -o -name __pycache__ \) -prune -exec rm -rf {} +
	rm -rf $(VENV_NAME) *.eggs *.egg-info dist build .cache

install: venv
	${PYTHON} setup.py install