import hashlib
import json
import logging

import dataiku
from lal.base_classifier import BaseClassifier


class TabularClassifier(BaseClassifier):
    @property
    def type(self):
        return 'tabular'

    logger = logging.getLogger(__name__)

    def __init__(self):
        super(TabularClassifier, self).__init__()
        self.unlabeled_df = dataiku.Dataset(self.config["unlabeled"]).get_dataframe()
        self.hash_to_index = {}
        for index, row in self.unlabeled_df.iterrows():
            self.hash_to_index[hashlib.md5(row.to_csv().encode('utf-8')).hexdigest()] = index

        self.queries_ds = dataiku.Dataset(self.config["queries_ds"])

    def get_sample_by_id(self, sample_id):
        self.logger.info('Reading row from: ' + str(sample_id))
        res = self.unlabeled_df.loc[self.hash_to_index[sample_id]].to_json()
        return json.loads(res)

    def get_all_sample_ids(self):
        return set(self.hash_to_index.keys())
