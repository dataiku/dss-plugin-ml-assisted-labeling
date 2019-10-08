from flask import request, jsonify

from lal.lal_handler import LALHandler

application_handler = LALHandler()


@app.route('/get-image-base64')
def get_image():
    path = request.args.get('path')
    return jsonify(application_handler.get_image(path))


@app.route('/sample')
def get_sample():
    return jsonify(application_handler.get_sample())


@app.route('/skip')
def skip_sample():
    return jsonify(application_handler.get_sample())


@app.route('/classify', methods=['POST'])
def classify():
    req_data = request.get_json()
    return jsonify(application_handler.classify(req_data))
