.PHONY: all build test precommit clean

all: build

build:
	python3 build/build.py

test: build
	node persona/tests/run.js

precommit: build test

clean:
	@true
