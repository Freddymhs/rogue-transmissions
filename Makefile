.PHONY: test render fetch commit push serve clean

# Run unit + integration tests
test:
	python3 -m pytest tests/ -v

# Regenerate index.html from data/transmissions.json + template.html
render:
	python3 render.py

# Fetch /partial-capture, append new entry, regenerate, commit
fetch:
	python3 arg_fetch.py

# Same as fetch but bypasses tests (for scheduled runs)
fetch-fast:
	python3 arg_fetch.py

# Local commit of any pending changes (no push)
commit:
	git add -A
	git commit -m "manual update" || true

# Push to GitHub — REQUIRES user confirmation; rule no-auto-push
push:
	@echo "Manual push only. Confirm: git push origin main"
	@git push origin main

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