# Makefile variables set automatically
plugin_id=`cat plugin.json | python -c "import sys, json; print(str(json.load(sys.stdin)['id']).replace('/',''))"`
plugin_version=`cat plugin.json | python -c "import sys, json; print(str(json.load(sys.stdin)['version']).replace('/',''))"`
archive_file_name="dss-plugin-${plugin_id}-${plugin_version}.zip"
remote_url=`git config --get remote.origin.url`
last_commit_id=`git rev-parse HEAD`


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

PYTHON ?= python3
UV ?= uv
REQUIREMENTS_GENERATOR = $(UV) run --no-project --python 3.11 python scripts/generate_requirements.py
PLUGIN_GENERATOR = $(UV) run --no-project --python 3.11 python scripts/generate_plugin.py

define run_tests
	@set -e; tmp=$$(mktemp); trap 'rm -f "$$tmp"' EXIT; \
		$(REQUIREMENTS_GENERATOR) --group dev $(1) > "$$tmp"; \
		PYTHONPATH="$(CURDIR)/python-lib$${PYTHONPATH:+:$$PYTHONPATH}" \
		$(UV) run --no-project --isolated --python $(PYTHON) \
			--with-requirements code-env/python/spec/requirements.txt --with-requirements "$$tmp" \
			python -m pytest $(2) --alluredir=tests/allure_report
endef

.PHONY: plugin-json check-plugin-json check-plugin-head requirements check-requirements tests unit-tests integration-tests integration-refresh-test

plugin-json:
	@set -e; tmp=$$(mktemp); trap 'rm -f "$$tmp"' EXIT; \
		$(PLUGIN_GENERATOR) > "$$tmp"; cat "$$tmp" > plugin.json

check-plugin-json:
	@$(PLUGIN_GENERATOR) --check

check-plugin-head:
	@$(PLUGIN_GENERATOR) --check-head
	@git cat-file -e HEAD:scripts/generate_plugin.py 2>/dev/null && \
		git diff --quiet HEAD -- plugin.json pyproject.toml scripts/generate_plugin.py || \
		(echo "Commit plugin metadata and its generator before packaging"; exit 1)

requirements:
	@set -e; tmp=$$(mktemp); trap 'rm -f "$$tmp"' EXIT; \
		$(REQUIREMENTS_GENERATOR) > "$$tmp"; cat "$$tmp" > code-env/python/spec/requirements.txt

check-requirements:
	@$(REQUIREMENTS_GENERATOR) --check

unit-tests: check-requirements check-plugin-json
	@$(PYTHON) -c 'import json, sys; v = "PYTHON{}{}".format(*sys.version_info[:2]); accepted = json.load(open("code-env/python/desc.json"))["acceptedPythonInterpreters"]; print("Python version {} is {}in acceptedPythonInterpreters".format(v, "" if v in accepted else "not ")); sys.exit(v not in accepted)'
	$(call run_tests,,tests --ignore=tests/python/integration)

integration-tests: check-requirements check-plugin-json
	$(call run_tests,--group integration,tests/python/integration --ignore=tests/python/integration/test_refresh_fixture.py)

integration-refresh-test: check-requirements check-plugin-json
	$(call run_tests,--group integration,tests/python/integration/test_refresh_fixture.py)

tests: unit-tests integration-tests

dist-clean:
	rm -rf dist
