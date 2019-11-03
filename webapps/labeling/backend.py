from flask import request, jsonify

from dataiku.customwebapp import get_webapp_config_filename
from lal.image_classifier import ImageClassifier
from lal.lal_handler import LALHandler
from lal.tabular_classifier import TabularClassifier

config_name = get_webapp_config_filename()
if config_name == 'webapp-tabular.json':
    lal_handler = LALHandler(TabularClassifier())
if config_name == 'webapp-image.json':
    lal_handler = LALHandler(ImageClassifier())


@app.route('/sample')
def get_sample():
    return jsonify(lal_handler.get_sample())


@app.route('/skip', methods=['POST'])
def skip_sample():
    req_data = request.get_json()
    return jsonify(lal_handler.skip(req_data))


@app.route('/back', methods=['POST'])
def back():
    req_data = request.get_json()
    resp = lal_handler.back(req_data)
    print("HOHOHOHO {0}".format(type(resp)))
    return jsonify(resp)


@app.route('/classify', methods=['POST'])
def classify():
    req_data = request.get_json()
    return jsonify(lal_handler.classify(req_data))
