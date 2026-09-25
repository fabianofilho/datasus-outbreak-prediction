install:
	pip install -r requirements.txt

install-dev: install
	pip install "pytest>=8"

run:
	streamlit run app.py

test:
	python -m pytest tests/ -v

download-demo:
	python scripts/download_all.py --state RJ --year 2022

cache:
	python scripts/build_cache.py

.PHONY: install install-dev run test download-demo cache
