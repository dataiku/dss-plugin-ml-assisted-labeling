import logging
from time import time
from typing import TypeVar

import numpy as np
import pandas as pd

import dataiku
from dataiku.core import schema_handling
from dataiku.customwebapp import *
from lal.base_classifier import BaseClassifier

C = TypeVar('C', bound=BaseClassifier)


class LALHandler(object):
    logger = logging.getLogger(__name__)
    labels_required_schema = [
        {"name": "date", "type": "date"},
        {"name": "id", "type": "string"},
        {"name": "label", "type": "string"},
        {"name": "comment", "type": "string"},
        {"name": "session", "type": "int"},
        {"name": "annotator", "type": "string"}
    ]

    def __init__(self, classifier, is_multiuser=True):
        """
        :type classifier: C
        """
        super(LALHandler, self).__init__()
        self.config = get_webapp_config()
        self.is_multiuser = is_multiuser
        self.classifier = classifier
        self._skipped = {}
        self.all_queries_ids = self.read_queries_ids()

        self.labels_ds = dataiku.Dataset(self.config["labels_ds"])
        self.labels_df = self.prepare_label_dataset(self.labels_ds)

    @property
    def skipped(self):
        if self.is_multiuser:
            return self._skipped.setdefault(self.current_user, set())
        else:
            return self._skipped.setdefault(None, set())

    @property
    def labels(self):
        return self.labels_df[self.labels_df.annotator == self.current_user]

    @property
    def current_user(self):
        return dataiku.api_client().get_auth_info()['authIdentifier']

    @property
    def remaining(self):
        if self.all_queries_ids is None:
            self.logger.info("Serving random queries")
            return list(self.classifier.get_all_sample_ids() - set(self.labels.id.values) - self.skipped)
        else:
            self.logger.info("Serving ordered queries")
            return [i for i in self.all_queries_ids if (i not in set(self.labels.id.values) and i not in self.skipped)]

    def calculate_stats(self):
        total_count = len(self.classifier.get_all_sample_ids())
        stats = {
            "labelled": len(self.labels),
            "total": total_count,
            "skipped": len(self.skipped)
        }
        return stats

    def classify(self, data):
        self.logger.info("Classifying: %s" % json.dumps(data))
        if 'id' not in data:
            message = "Classification data doesn't containg sample ID"
            self.logger.error(message)
            raise ValueError(message)

        self.labels_df = self.labels_df[self.labels_df.id != data.get('id')]

        self.labels_df = self.labels_df.append({
            'date': time(),
            'id': data.get('id'),
            'label': json.dumps(data.get('class')),
            'comment': data.get('comment'),
            'session': 0,
            'annotator': self.current_user,
        }, ignore_index=True)

        self.labels_ds.write_with_schema(self.labels_df)
        self.logger.info("Wrote labels Dataframe of shape:  %s" % str(self.labels_df.shape))

        return self.get_sample()

    def is_stopping_criteria_met(self):
        return len(self.remaining) <= 0

    def get_sample(self, sample_id=None):
        self.logger.info("Getting sample, sample_id: {0}".format(sample_id))
        stats = self.calculate_stats()
        if self.is_stopping_criteria_met():
            return {
                **{"is_done": True},
                **stats
            }
        if not sample_id:
            remaining = self.remaining
            if len(remaining) > 0:
                sample_id = remaining[-1]
            else:
                sample_id = None
        result = {
            "type": self.classifier.type,
            "data": self.classifier.get_sample_by_id(sample_id) if sample_id else None,
            "is_done": False,
            "id": sample_id
        }
        return {**result, **stats}

    def back(self, data):
        current_id = data['current']
        label_date = None
        if current_id in self.labels.id.values:
            label_date = self.labels[self.labels.id == current_id].date.values[0]

        sorted_labels = self.labels.sort_values('date', ascending=False)

        if label_date is not None:
            sorted_labels = sorted_labels[sorted_labels.date < label_date]

        previous = sorted_labels.where((pd.notnull(sorted_labels)), None).astype('object').to_dict(orient='records')[0]

        result = {
            "label": {"class": json.loads(previous['label']), "comment": previous['comment']},
            "type": self.classifier.type,
            "is_first": len(sorted_labels) == 1,
            "id": previous['id'],
            "data": self.classifier.get_sample_by_id(previous['id']),

        }
        stats = self.calculate_stats()
        return {**result, **stats}

    def skip(self, data):
        self.skipped.add(data['id'])
        return self.get_sample()

    def read_queries_ids(self):
        self.logger.info("Trying to read and sort queries from {0}".format(self.config["queries_ds"]))
        queries_ds = dataiku.Dataset(self.config["queries_ds"])
        try:
            return queries_ds.get_dataframe().sort_values('uncertainty')['id'].tolist()
        except Exception as e:
            self.logger.info("Queries dataset is not initialized: {0}".format(e))
            return None

    def prepare_label_dataset(self, dataset):

        try:
            dataset_schema = dataset.read_schema()
            dataset_schema_columns = {c['name'] for c in dataset_schema}

            if not self.__labels_required_columns.issubset(dataset_schema_columns):
                raise ValueError(
                    "The target dataset should have columns: {}. The provided dataset has columns: {}. "
                    "Please edit the schema in the dataset settings.".format(
                        ', '.join(self.__labels_required_columns), ', '.join(dataset_schema_columns)))

            current_df = dataset.get_dataframe()
        except:
            self.logger.info("{} probably empty".format(dataset.name))
            current_df = pd.DataFrame(columns=self.__labels_required_columns, index=[])
            for col in self.labels_required_schema:
                n = col["name"]
                t = col["type"]
                t = schema_handling.DKU_PANDAS_TYPES_MAP.get(t, np.object_)
                current_df[n] = current_df[n].astype(t)
        return current_df

    @property
    def __labels_required_columns(self):
        return {c['name'] for c in self.labels_required_schema}
