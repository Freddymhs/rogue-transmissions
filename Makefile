.PHONY: test render fetch commit serve clean

# Run unit + integration tests
test:
	python3 -m pytest tests/ -v

# Regenerate index.html from data/transmissions.json + template.html
render:
	python3 render.py

# Fetch /partial-capture, append new entry, regenerate, commit
fetch:
	python3 arg_fetch.py

# Local commit of any pending changes (no push)
commit:
	git add -A
	git commit -m "manual update" || true

# Serve locally for preview
serve:
	python3 -m http.server 8000

# Clean generated artifacts
clean:
	rm -f index.html
	rm -rf __pycache__ .pytest_cache
	find . -name "*.pyc" -delete

# Run tests + render in one shot (CI-style)
ci: test render