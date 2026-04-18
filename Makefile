refresh-deps:
	pip-compile \
	  --generate-hashes \
	  --output-file requirements.txt \
	  pyproject.toml

venv-start:
	source .venv/Scripts/activate

run-backend:
	python far_out/manage.py runserver

run-site: run-backend
	npm run build && npm run start
