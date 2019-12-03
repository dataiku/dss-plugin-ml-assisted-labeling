import logging
from base64 import b64encode

import pandas as pd

from lal.classifiers.base_classifier import BaseClassifier


class SoundClassifier(BaseClassifier):
    logger = logging.getLogger(__name__)

    def __init__(self, folder, queries_df, config):
        """

        :type folder: dataiku.core.managed_folder.Folder
        """
        self.folder = folder
        self.queries_df = queries_df
        super(SoundClassifier, self).__init__(queries_df, config)

    def validate_config(self, config):
        config = super().validate_config(config)
        if "unlabeled" not in config:
            raise ValueError("Sound folder not specified. Go to settings tab.")
        return config

    def get_enriched_item_by_id(self, sid):
        self.logger.info('Reading sound from: ' + str(sid))
        with self.folder.get_download_stream(sid) as s:
            data = b64encode(s.read())

        self.logger.info("Read: {0}, {1}".format(len(data), type(data)))
        return data.decode('utf-8')

    def get_raw_item_by_id(self, sid):
        return {"path": sid}

    def raw_row_to_id(self, raw):
        return raw['path']

    def get_initial_df(self):
        return pd.DataFrame(self.folder.list_paths_in_partition(), columns=["path"])

    @property
    def type(self):
        return "sound"
