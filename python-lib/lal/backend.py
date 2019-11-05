from flask import request, jsonify

from lal.lal_handler import LALHandler


def define_endpoints(app, classifier):
    handler = LALHandler(classifier)

    @app.route('/sample')
    def get_sample():
        return jsonify(handler.get_sample())

    @app.route('/skip', methods=['POST'])
    def skip_sample():
        req_data = request.get_json()
        return jsonify(handler.skip(req_data))

    @app.route('/back', methods=['POST'])
    def back():
        req_data = request.get_json()
        resp = handler.back(req_data)
        return jsonify(resp)

    @app.route('/classify', methods=['POST'])
    def classify():
        req_data = request.get_json()
        return jsonify(handler.classify(req_data))
