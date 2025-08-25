PY=python3

.PHONY: scrape build deploy

scrape:
	$(PY) scrape.py

build: scrape
	@echo "catalog.json regenerated"

deploy: build
	@echo "Deploy step should publish index.html and catalog.json"

