import logging
from collections import namedtuple

import numpy as np

import dataiku
from dataiku.customwebapp import *

class LALHandler(object):
    logger = logging.getLogger(__name__)

    def __init__(self, classifier):
        """

        :type classifier: lal.base_classifier.BaseClassifier
        """
        super(LALHandler, self).__init__()
        self.config = get_webapp_config()
        self.skipped = set()
        self.current_user = dataiku.api_client().get_auth_info()['authIdentifier']
        self._queries_df = None
        self.classifier = classifier

    @property
    def remaining(self):
        try:
            self.logger.info("Trying to sort queries by uncertainty")
            queries_df = self.queries_df.sort_values('uncertainty')['id']
            remaining = queries_df[~queries_df.isin(self.classifier.get_labeled_sample_ids())].unique().tolist()
            return remaining
        except:
            self.logger.info("Not taking into account uncertainty, serving random queries")
            return list(self.classifier.get_all_sample_ids() - self.classifier.get_labeled_sample_ids() - self.skipped)

    def get_sample(self, sample_id=None):
        self.logger.info("Getting sample")
        stats = self.calculate_stats()
        if self.is_stopping_criteria_met():
            return {**{
                "is_done": True
            }, **self.calculate_stats()}
        if not sample_id:
            if len(self.remaining) > 0:
                sample_id = self.remaining[-1]
            else:
                sample_id = None
        result = {
            "type": self.classifier.type,
            "data": self.classifier.get_sample_by_id(sample_id) if sample_id else None,
            "is_done": False,
            "id": sample_id
        }
        return {**result, **stats}

    def calculate_stats(self):
        total_count = len(self.classifier.get_all_sample_ids())
        labelled_count = len(self.classifier.get_labeled_sample_ids())
        # -1 because the current is not counted :
        by_category = self.classifier.labels_df['class'].value_counts().to_dict()
        stats = {
            "labelled": labelled_count,
            "total": total_count,
            "skipped": len(self.skipped),
            "byCategory": by_category}
        return stats

    def classify(self, data):
        self.logger.info("Classifying: %s" % json.dumps(data))
        if 'id' not in data:
            message = "Classification data doesn't containg sample ID"
            self.logger.error(message)
            raise ValueError(message)

        self.classifier.add_label(data)
        if data['id'] in self.remaining:
            self.remaining.remove(data['id'])
        self.classifier.labels_ds.write_with_schema(self.classifier.labels_df)
        self.logger.info("Wrote labels Dataframe of shape:  %s" % str(self.classifier.labels_df.shape))

        return self.get_sample()

    def is_stopping_criteria_met(self):
        return len(self.remaining) <= 0

    def back(self, data):
        self.logger.info("BACK, {}".format(data))
        current_id = data['current']

        user_df = self.classifier.labels_df[self.classifier.labels_df['annotator'] == self.current_user]
        if current_id in user_df['id'].values:
            current_date = user_df[user_df.id == current_id]['date'].values[0]
            self.logger.info("Current date: {}".format(current_date))
            user_df = user_df[user_df.date < current_date]
        logging.info("User_DF: {}".format(user_df.shape[0]))
        previous = \
            user_df.sort_values('date', ascending=False).head(1).replace({np.nan: None}).to_dict(orient='records')[0]

        result = {
            "label": {
                "class": previous['class'],
                "comment": previous['comment'],
            },
            "type": self.classifier.type,
            "is_first": user_df.shape[0] <= 1,
            "id": previous['id'],
            "data": self.classifier.get_sample_by_id(previous['id']),

        }
        stats = self.calculate_stats()
        return {**result, **stats}

    def skip(self, data):
        self.skipped.add(data['id'])
        return self.get_sample()

    @property
    def queries_df(self):
        if self._queries_df:
            return self._queries_df
        try:
            self._queries_df = dataiku.Dataset(self.config["queries_ds"]).get_dataframe()
        except:
            self._queries_df = None

        return self._queries_df
