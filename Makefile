.PHONY: all build precommit clean

all: build

build:
	python3 build/build.py

precommit: build

clean:
	@true
