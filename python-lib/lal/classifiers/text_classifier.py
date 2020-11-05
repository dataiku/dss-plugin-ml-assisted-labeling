import json
import logging

import pandas as pd

TEXT_COLUMN_DEFAULT_LABEL = 'text'


from lal.classifiers.base_classifier import TableBasedDataClassifier


class TextClassifier(TableBasedDataClassifier):
    logger = logging.getLogger(__name__)

    def __init__(self, initial_df, queries_df, config=None):
        self.__initial_df = initial_df
        self.text_column = config["text_column"]
        super(TextClassifier, self).__init__(queries_df, config)

    def get_initial_df(self):
        return self.__initial_df.rename({self.text_column: TEXT_COLUMN_DEFAULT_LABEL}, axis='columns')[TEXT_COLUMN_DEFAULT_LABEL].to_frame()

    def serialize_label(self, label):
        return json.dumps(label)

    def deserialize_label(self, label):
        return json.loads(label)

    @property
    def type(self):
        return 'text'

    @staticmethod
    def format_labels_for_stats(raw_labels_series):
        labels = []
        return pd.Series()
        for v in raw_labels_series.values:
            if pd.notnull(v):
                labels += [a['label'] for a in json.loads(v) if a['label']]
        return pd.Series(labels)
