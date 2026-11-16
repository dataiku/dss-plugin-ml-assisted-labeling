# Makefile variables set automatically
plugin_id=`cat plugin.json | python -c "import sys, json; print(str(json.load(sys.stdin)['id']).replace('/',''))"`
plugin_version=`cat plugin.json | python -c "import sys, json; print(str(json.load(sys.stdin)['version']).replace('/',''))"`
archive_file_name="dss-plugin-${plugin_id}-${plugin_version}.zip"
remote_url=`git config --get remote.origin.url`
last_commit_id=`git rev-parse HEAD`


# Package committed plugin files into dist/, excluding tests and adding release metadata.
plugin: check-plugin-json check-plugin-head
	@echo "[START] Archiving plugin to dist/ folder..."
	@cat plugin.json | json_pp > /dev/null
	@rm -rf dist
	@mkdir dist
	@git archive -v -9 --format zip -o dist/${archive_file_name} HEAD
	@zip --delete dist/${archive_file_name} "tests/*"
	@set -e; tmp=$$(mktemp -d); trap 'rm -rf "$$tmp"' EXIT; \
		echo "{\"remote_url\":\"${remote_url}\",\"last_commit_id\":\"${last_commit_id}\"}" > "$$tmp/release_info.json"; \
		archive="$(CURDIR)/dist/"${archive_file_name}; \
		(cd "$$tmp" && zip -u "$$archive" release_info.json)
	@echo "[SUCCESS] Archiving plugin to dist/ folder: Done!"

# Select the test interpreter and the tool used to export dependencies.
PYTHON ?= python3
UV ?= uv
REQUIREMENTS_EXPORT = $(UV) export --no-default-groups --no-hashes --no-emit-project
PLUGIN_GENERATOR = $(PYTHON) scripts/generate_plugin.py

# Install exported dependencies in a temporary environment, then run pytest.
define run_tests
	@set -e; tmp=$$(mktemp -d); trap 'rm -rf "$$tmp"' EXIT; \
		$(PYTHON) -m venv "$$tmp"; \
		"$$tmp/bin/python" -m pip install -r $(1); \
		PATH="$$tmp/bin:$$PATH" PYTHONPATH="$(CURDIR)/python-lib$${PYTHONPATH:+:$$PYTHONPATH}" \
			"$$tmp/bin/python" -m pytest $(2) --alluredir=tests/allure_report
endef

.PHONY: plugin-json check-plugin-json check-plugin-head requirements check-requirements tests unit-tests integration-tests integration-refresh-test

# Generate plugin.json from pyproject.toml.
plugin-json:
	@set -e; tmp=$$(mktemp); trap 'rm -f "$$tmp"' EXIT; \
		$(PLUGIN_GENERATOR) > "$$tmp"; cat "$$tmp" > plugin.json

# Verify that plugin.json matches pyproject.toml.
check-plugin-json:
	@$(PLUGIN_GENERATOR) --check

# Ensure packaging uses committed, consistent plugin metadata and generator files.
check-plugin-head:
	@$(PLUGIN_GENERATOR) --check-head
	@git cat-file -e HEAD:scripts/generate_plugin.py 2>/dev/null && \
		git diff --quiet HEAD -- plugin.json pyproject.toml scripts/generate_plugin.py || \
		(echo "Commit plugin metadata and its generator before packaging"; exit 1)

# Export the DSS, unit-test and integration-test requirements from pyproject.toml.
requirements:
	@set -e; tmp=$$(mktemp -d); trap 'rm -rf "$$tmp"' EXIT; \
		$(REQUIREMENTS_EXPORT) > "$$tmp/runtime"; \
		$(REQUIREMENTS_EXPORT) --group dev > "$$tmp/unit"; \
		$(REQUIREMENTS_EXPORT) --group dev --group integration > "$$tmp/integration"; \
		cat "$$tmp/runtime" > code-env/python/spec/requirements.txt; \
		cat "$$tmp/unit" > tests/python/unit/requirements.txt; \
		cat "$$tmp/integration" > tests/python/integration/requirements.txt

# Verify that the generated requirements are up to date.
check-requirements:
	@set -e; tmp=$$(mktemp); trap 'rm -f "$$tmp"' EXIT; \
		$(REQUIREMENTS_EXPORT) > "$$tmp"; \
		cmp -s "$$tmp" code-env/python/spec/requirements.txt || \
		(echo "Generated requirements are out of date; run make requirements"; exit 1); \
		$(REQUIREMENTS_EXPORT) --group dev > "$$tmp"; \
		cmp -s "$$tmp" tests/python/unit/requirements.txt || \
		(echo "Unit-test requirements are out of date; run make requirements"; exit 1); \
		$(REQUIREMENTS_EXPORT) --group dev --group integration > "$$tmp"; \
		cmp -s "$$tmp" tests/python/integration/requirements.txt || \
		(echo "Integration-test requirements are out of date; run make requirements"; exit 1)

# Check the interpreter is supported and run tests that do not require DSS.
unit-tests:
	@$(PYTHON) -c 'import json, sys; v = "PYTHON{}{}".format(*sys.version_info[:2]); accepted = json.load(open("code-env/python/desc.json"))["acceptedPythonInterpreters"]; print("Python version {} is {}in acceptedPythonInterpreters".format(v, "" if v in accepted else "not ")); sys.exit(v not in accepted)'
	$(call run_tests,tests/python/unit/requirements.txt,tests --ignore=tests/python/integration)

# Run DSS integration tests, excluding the prepared-project refresh scenario.
integration-tests:
	$(call run_tests,tests/python/integration/requirements.txt,tests/python/integration --ignore=tests/python/integration/test_refresh_fixture.py)

# Run the DeepHub refresh tests using a dedicated prepared DSS project.
integration-refresh-test:
	$(call run_tests,tests/python/integration/requirements.txt,tests/python/integration/test_refresh_fixture.py)

# Run unit tests and the standard DSS integration tests.
tests: unit-tests integration-tests

# Remove the packaged plugin archive directory.
dist-clean:
	rm -rf dist
