build: clean
	python -m build --sdist

publish: build
	twine upload -r pypi dist/*

install: build
	pip uninstall -y nuxt
	pip install dist/nuxt*

clean:
	@rm -rf dist *.egg-info