SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SPHINXPROJ    = sanic-jwt
SOURCEDIR     = docs/source
BUILDDIR      = docs/build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	@echo "test - run tests with coverage"
	@echo "release - package and upload a release"

.PHONY: help Makefile

%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

test:
	python setup.py test

release: clean
	python setup.py sdist upload
	python setup.py bdist_wheel upload
