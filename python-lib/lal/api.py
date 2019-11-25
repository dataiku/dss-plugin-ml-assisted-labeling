import logging

from flask import request, jsonify

import dataiku


def define_endpoints(app, classifier_cls):
    def handler():
        logging.info("Creating Handler")

        request_headers = dict(request.headers)
        auth_info = dataiku.api_client().get_auth_info_from_browser_headers(request_headers)

        from lal.handlers.dataiku_lal_handler import DataikuLALHandler
        return DataikuLALHandler(classifier_cls, user=auth_info["authIdentifier"])

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
