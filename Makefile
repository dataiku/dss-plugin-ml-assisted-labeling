PLUGIN_VERSION=3.0.0
PLUGIN_ID=ml-assisted-labeling

all:
	cat plugin.json|json_pp > /dev/null
	rm -rf dist
	mkdir dist
	zip -r dist/dss-plugin-${PLUGIN_ID}-${PLUGIN_VERSION}.zip apps code-env custom-recipes data js python-lib python-steps python-triggers resource webapps plugin.json
