#!/usr/bin/env make

FILES = azero.py game.py model.py

.PHONY: all play cprof lprof shell test

all: test

play: play.py
	python $^

cprof: azero.py
	python -m cProfile -s cumtime azero.py > $^.cprof
	head -20 < $^.cprof

lprof: azero.py
	kernprof -l -b $^
	python -m line_profiler $^.lprof

shell: azero.py
	ipython -i $^

lint:
	flake8 $(FILES)

test: lint
	python -m unittest
