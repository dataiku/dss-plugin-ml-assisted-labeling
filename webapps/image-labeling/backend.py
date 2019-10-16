from flask import request, jsonify

from lal.image_classifier import ImageClassifier
from lal.lal_handler import LALHandler

lal_handler = LALHandler(ImageClassifier())

@app.route('/sample')
def get_sample():
    return jsonify(lal_handler.get_sample())


@app.route('/skip')
def skip_sample():
    return jsonify(lal_handler.get_sample())


@app.route('/classify', methods=['POST'])
def classify():
    req_data = request.get_json()
    return jsonify(lal_handler.classify(req_data))
