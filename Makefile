.PHONY: test format clean build publish publish-test release

test:
	python -m unittest discover -s tests -p 'test_*.py'

format:
	python -m black .


# --- Publishing --- #

# Get version from the package itself
VERSION := $(shell python -c "from autopr import __version__; print(__version__)")

clean:
	@echo "Cleaning up build artifacts..."
	@rm -rf dist build *.egg-info autopr_cli.egg-info

build: clean
	@echo "Building sdist and wheel for version $(VERSION)..."
	python -m build

publish-test: build
	@echo "You are about to publish version $(VERSION) to TestPyPI."
	@read -p "Are you sure? (y/N) " -n 1 -r; \
	echo; \
	if [[ ! $$REPLY =~ ^[Yy]$$ ]]; then \
	    echo "Publishing to TestPyPI aborted."; \
	    exit 1; \
	fi
	@echo "Uploading to TestPyPI..."
	twine upload --repository testpypi dist/*

publish: build # Depends on build, clean is handled by build's dependency
	@echo "-----------------------------------------------------"
	@echo "You are about to publish version $(VERSION) to REAL PyPI."
	@echo "Consider running 'make publish-test' first."
	@echo "-----------------------------------------------------"
	@read -p "Are you absolutely sure you want to publish to PyPI? (y/N) " -n 1 -r; \
	echo; \
	if [[ ! $$REPLY =~ ^[Yy]$$ ]]; then \
	    echo "Publishing to PyPI aborted."; \
	    exit 1; \
	fi
	@echo "Uploading to PyPI..."
	twine upload dist/*

release: publish
	@echo "Creating git tag v$(VERSION)..."
	@git tag v$(VERSION)
	@echo "Version $(VERSION) published to PyPI and tagged."
	@echo "-----------------------------------------------------"
	@echo "IMPORTANT: Remember to push tags to remote:"
	@echo "  git push origin v$(VERSION)"
	@echo "  OR for all tags: git push --tags"
	@echo "-----------------------------------------------------" 