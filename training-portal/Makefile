all:

venv:
	python3.10 -m venv venv

update-packages:
	venv/bin/pip install -r requirements.txt

.PHONY: src/static

src/static:
	venv/bin/python src/manage.py collectstatic --no-input

.PHONY: requirements.txt

requirements.txt: requirements.in
	pip-compile $<

build-project: venv update-packages src/static

build-migrations:
	venv/bin/python src/manage.py makemigrations

clean-project:
	rm -rf src/project/__pycache__ src/project/*/__pycache__
	rm -rf src/project/*/*/__pycache__ src/project/*/*/*/__pycache__
	rm -f data/db.sqlite3 data/secret-key.txt
	rm -rf src/static
	rm -rf venv
