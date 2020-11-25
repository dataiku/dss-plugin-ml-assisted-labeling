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
        return self.__initial_df

    def clean_data_to_save(self, lab):
        return {
            'text': lab['text'],
            'startId': lab['startId'],
            'endId': lab['endId'],
            'label': lab['label']
        }

    def get_relevant_config(self):
        return {"text_column": self.text_column}

    def serialize_label(self, label):
        cleaned_labels = [self.clean_data_to_save(lab) for lab in label]
        return json.dumps(cleaned_labels)

    def deserialize_label(self, label):
        return json.loads(label)

    @property
    def type(self):
        return 'text'

    @property
    def is_dynamic(self):
        return True

    @staticmethod
    def format_labels_for_stats(raw_labels_series):
        labels = []
        for v in raw_labels_series.values:
            if pd.notnull(v):
                print(v)
                labels += [a['label'] for a in json.loads(v) if a['label']]
        return pd.Series(labels)
