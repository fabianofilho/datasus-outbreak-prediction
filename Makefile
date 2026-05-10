install:
	pip install -r requirements.txt

run:
	streamlit run app.py

test:
	pytest tests/ -v

download-demo:
	python scripts/download_all.py --state RJ --year 2022

cache:
	python scripts/build_cache.py

.PHONY: install run test download-demo cache
