import logging

from flask import request, jsonify


def define_endpoints(app, classifier_cls):

    def handler():
        logging.info("Creating Handler")
        from lal.handlers.dataiku_lal_handler import DataikuLALHandler
        return DataikuLALHandler(classifier_cls)

    @app.route('/batch')
    def get_sample():
        return jsonify(handler().get_batch())

    @app.route('/skip', methods=['POST'])
    def skip_sample():
        req_data = request.get_json()
        return jsonify(handler().skip(req_data))

    @app.route('/back', methods=['POST'])
    def back():
        req_data = request.get_json()
        resp = handler().back(req_data.get('id'))
        return jsonify(resp)

    @app.route('/label', methods=['POST'])
    def label():
        req_data = request.get_json()
        return jsonify(handler().label(req_data))
