# USDM4 FHIR

# Install

```pip install usdm4_fhir```

# Build Package

Build steps for deployment to pypi.org

- Run `pytest`, ensure coverage and all tests pass
- Run `ruff format`
- Run `ruff check`, ensure no errors
- Build with `python3 -m build --sdist --wheel`
- Upload to pypi.org using `twine upload dist/*`