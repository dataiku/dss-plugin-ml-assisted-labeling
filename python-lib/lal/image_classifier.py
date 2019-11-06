import logging
from base64 import b64encode

import dataiku
from lal.base_classifier import BaseClassifier


class ImageClassifier(BaseClassifier):
    logger = logging.getLogger(__name__)

    def __init__(self):
        super(ImageClassifier, self).__init__()
        self.folder = dataiku.Folder(self.config["folder"])

    def read_config(self):
        config = super().read_config()
        if "folder" not in config:
            raise ValueError("Image folder not specified. Go to settings tab.")
        return config

    def get_sample_by_id(self, sid):
        self.logger.info('Reading image from: ' + str(sid))
        with self.folder.get_download_stream(sid) as s:
            data = b64encode(s.read())

        self.logger.info("Read: {0}, {1}".format(len(data), type(data)))
        return data.decode('utf-8')

    def get_all_sample_ids(self):
        return set(self.folder.list_paths_in_partition())

    @property
    def type(self):
        return "image"
