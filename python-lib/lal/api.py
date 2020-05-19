import traceback

from flask import request, jsonify
from werkzeug.exceptions import HTTPException

import dataiku


def define_endpoints(app, handler):

    def get_user():
        request_headers = dict(request.headers)
        auth_info = dataiku.api_client().get_auth_info_from_browser_headers(request_headers)
        user = auth_info["authIdentifier"]
        return user

    @app.errorhandler(Exception)
    def handle_error(e):
        code = 500
        if isinstance(e, HTTPException):
            code = e.code
        return jsonify(error=str(e), trace=traceback.format_exc()), code

    @app.route('/batch')
    def get_sample():
        return jsonify(handler.get_batch(get_user()))

    @app.route('/skip', methods=['POST'])
    def skip_sample():
        req_data = request.get_json()
        return jsonify(handler.skip(req_data, get_user()))

    @app.route('/back', methods=['POST'])
    def back():
        resp = handler.previous(request.get_json().get('labelId'), get_user())
        return jsonify(resp)

    @app.route('/next', methods=['POST'])
    def next():
        resp = handler.next(request.get_json().get('labelId'), get_user())
        return jsonify(resp)

    @app.route('/first', methods=['POST'])
    def first():
        return jsonify(handler.first(get_user()))

    @app.route('/label', methods=['POST'])
    def label():
        req_data = request.get_json()
        return jsonify(handler.label(req_data, get_user()))

    @app.route('/config', methods=['GET'])
    def config():
        return jsonify(handler.get_config())
