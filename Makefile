PLUGIN_VERSION=1.0.0
PLUGIN_ID=ml-assisted-labeling

all:
	cat plugin.json|json_pp > /dev/null
	rm -rf dist
	mkdir dist
	zip -r dist/dss-plugin-${PLUGIN_ID}-${PLUGIN_VERSION}.zip code-env custom-recipes python-lib python-triggers resource/axios.js resource/dku-helper.js resource/vue.js resource/labeling-app webapps plugin.json
