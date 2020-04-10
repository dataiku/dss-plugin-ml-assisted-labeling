import logging
import traceback

from flask import request, jsonify
from werkzeug.exceptions import HTTPException

import dataiku


def define_endpoints(app, classifier_cls):
    def handler():
        logging.info("Creating Handler")

        request_headers = dict(request.headers)
        auth_info = dataiku.api_client().get_auth_info_from_browser_headers(request_headers)

        from lal.handlers.dataiku_lal_handler import DataikuLALHandler
        return DataikuLALHandler(classifier_cls, user=auth_info["authIdentifier"])

    @app.errorhandler(Exception)
    def handle_error(e):
        code = 500
        if isinstance(e, HTTPException):
            code = e.code
        return jsonify(error=str(e), trace=traceback.format_exc()), code

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

    @app.route('/config', methods=['GET'])
    def config():
        return jsonify(handler().get_config())
