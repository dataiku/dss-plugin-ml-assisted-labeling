# Makefile variables set automatically
plugin_id=`cat plugin.json | python -c "import sys, json; print(str(json.load(sys.stdin)['id']).replace('/',''))"`
plugin_version=`cat plugin.json | python -c "import sys, json; print(str(json.load(sys.stdin)['version']).replace('/',''))"`
archive_file_name="dss-plugin-${plugin_id}-${plugin_version}.zip"
remote_url=`git config --get remote.origin.url`
last_commit_id=`git rev-parse HEAD`


plugin:
	@echo "[START] Archiving plugin to dist/ folder..."
	@cat plugin.json | json_pp > /dev/null
	@rm -rf dist
	@mkdir dist
	@echo "{\"remote_url\":\"${remote_url}\",\"last_commit_id\":\"${last_commit_id}\"}" > release_info.json
	@git archive -v -9 --format zip -o dist/${archive_file_name} HEAD
	@zip --delete dist/${archive_file_name} "tests/*"
	@zip -u dist/${archive_file_name} release_info.json
	@rm release_info.json
	@echo "[SUCCESS] Archiving plugin to dist/ folder: Done!"

PYTHON ?= python3
UV ?= uv
UV_RUN = $(UV) run --isolated --locked --python $(PYTHON) --group dev
UV_EXPORT = $(UV) export --no-dev --no-hashes --no-emit-project --no-header

.PHONY: requirements check-requirements tests unit-tests integration-tests

requirements:
	@$(UV_EXPORT) --quiet --output-file code-env/python/spec/requirements.txt

check-requirements:
	@$(UV_EXPORT) --locked --quiet | cmp -s - code-env/python/spec/requirements.txt || (echo "Generated requirements are out of date; run make requirements"; exit 1)

unit-tests: check-requirements
	@$(PYTHON) -c 'import json, sys; v = "PYTHON{}{}".format(*sys.version_info[:2]); accepted = json.load(open("code-env/python/desc.json"))["acceptedPythonInterpreters"]; print("Python version {} is {}in acceptedPythonInterpreters".format(v, "" if v in accepted else "not ")); sys.exit(v not in accepted)'
	@PYTHONPATH="$(CURDIR)/python-lib$${PYTHONPATH:+:$$PYTHONPATH}" $(UV_RUN) python -m pytest tests --ignore=tests/python/integration --alluredir=tests/allure_report

integration-tests:
	@if find tests/python/integration -name 'test_*.py' -print -quit | grep -q .; then \
		PYTHONPATH="$(CURDIR)/python-lib$${PYTHONPATH:+:$$PYTHONPATH}" $(UV_RUN) --with-requirements tests/python/integration/requirements.txt python -m pytest tests/python/integration --alluredir=tests/allure_report; \
	else \
		echo "No integration tests found"; \
	fi

tests: unit-tests integration-tests

dist-clean:
	rm -rf dist
