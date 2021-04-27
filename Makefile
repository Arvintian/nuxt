build:
	@rm -rf dist || true
	python setup.py egg_info --egg-base /tmp sdist

publish:
	@rm -rf dist || true
	python setup.py egg_info --egg-base /tmp sdist upload -r pypi


install: build
	pip uninstall -y nuxt
	pip install dist/nuxt*

clean:
	@rm -rf dist