import hashlib
import json
import logging
from datetime import datetime

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
        self.current_user = dataiku.api_client().get_auth_info()['authIdentifier']

    def add_label(self, annotaion):
        sample_id = annotaion.get('id')
        cat = annotaion.get('class')
        comment = annotaion.get('comment')
        self.labels_df = self.labels_df[self.labels_df.id != sample_id]

        self.labels_df = self.labels_df.append({
            'date': datetime.now(),
            'id': sample_id,
            'class': cat,
            'comment': comment,
            'session': 0,
            'annotator': self.current_user,
        }, ignore_index=True)

    @property
    def labels_required_schema(self):
        # TODO: Named tuple?
        return [
            {"name": "date", "type": "date"},
            {"name": "id", "type": "string"},
            {"name": "class", "type": "string"},
            {"name": "comment", "type": "string"},
            {"name": "session", "type": "int"},
            {"name": "annotator", "type": "string"}]

    def get_sample_by_id(self, sample_id):
        self.logger.info('Reading row from: ' + str(sample_id))
        res = self.unlabeled_df.loc[self.hash_to_index[sample_id]].to_json()
        return json.loads(res)

    def get_all_sample_ids(self):
        self.logger.info("Reading queries_ds")
        try:
            self.logger.info(self.queries_ds.get_dataframe()['id'].shape)
            return set(self.queries_ds.get_dataframe()['id'].tolist())
        except:
            self.logger.info("Couldn't read queries_ds")
            return set(self.hash_to_index.keys())

    def get_labeled_sample_ids(self):
        return set(self.labels_df[self.labels_df['annotator'] == self.current_user]['id'])
