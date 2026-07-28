PYTHONPATH=src

.PHONY: validate stats build test clean

validate:
	PYTHONPATH=$(PYTHONPATH) python -m ckb.cli validate

stats:
	PYTHONPATH=$(PYTHONPATH) python -m ckb.cli stats

build:
	PYTHONPATH=$(PYTHONPATH) python -m ckb.cli build --output exports

test:
	PYTHONPATH=$(PYTHONPATH) python -m unittest discover -s tests -v

clean:
	rm -rf exports/*
	touch exports/.gitkeep
