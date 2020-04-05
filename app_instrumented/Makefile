.DEFAULT_GOAL := run

.PHONY: run
run:
	. venv/bin/activate; flask run

.PHONY: install
install: venv
	venv/bin/pip install -r requirements.txt

.PHONY: venv
venv:
	python3 -m venv venv
