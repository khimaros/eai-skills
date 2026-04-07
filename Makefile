.PHONY: all build test wait-publish precommit clean

all: build

build:
	python3 build/build.py

test: build
	node persona/tests/run.js

wait-publish:
	build/wait_publish.sh

precommit: build test

clean:
	@true
