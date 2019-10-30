import logging

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
        self.current_user = dataiku.api_client().get_auth_info()['authIdentifier']
        self._queries_df = None
        self.classifier = classifier
        self.remaining = self.get_remaining_queries()

    def get_remaining_queries(self):
        try:
            self.logger.info("Trying to sort queries by uncertainty")
            queries_df = self.queries_df.sort_values('uncertainty')['id']
            remaining = queries_df[~queries_df.isin(self.classifier.get_labeled_sample_ids())].unique().tolist()
            return remaining
        except:
            self.logger.info("Not taking into account uncertainty, serving random queries")
            return list(self.classifier.get_all_sample_ids() - self.classifier.get_labeled_sample_ids())

    def get_sample(self, sid=None):
        self.logger.info("Getting sample")
        if self.is_stopping_criteria_met():
            return {
                "is_done": True
            }
        if not sid:
            if len(self.remaining) > 0:
                sid = self.remaining[-1]
            else:
                sid = None
        total_count = len(self.classifier.get_all_sample_ids())
        labelled_count = len(self.classifier.get_labeled_sample_ids())
        # -1 because the current is not counted :
        skipped_count = total_count - labelled_count - len(self.remaining)
        by_category = self.classifier.annotations_df['class'].value_counts().to_dict()
        result = {
            "is_done": False,
            "sid": sid,
            "data": self.classifier.get_sample_by_id(sid),
            "labelled": labelled_count,
            "total": total_count,
            "skipped": skipped_count,
            "byCategory": by_category
        }
        return result

    def classify(self, data):
        self.logger.info("Classifying: %s" % json.dumps(data))
        if 'sid' not in data:
            message = "Classification data doesn't containg sample ID"
            self.logger.error(message)
            raise ValueError(message)

        self.classifier.add_annotation(data)
        self.remaining.remove(data['sid'])
        self.classifier.annotations_ds.write_with_schema(self.classifier.annotations_df)
        self.logger.info("Wrote Annotations Dataframe of shape:  %s" % str(self.classifier.annotations_df.shape))

        return self.get_sample()

    def is_stopping_criteria_met(self):
        return len(self.get_remaining_queries()) < 0

    def back(self, data):
        self.logger.info("BACK, {}".format(data))
        current_id = data['current']

        user_df = self.classifier.annotations_df[self.classifier.annotations_df['annotator'] == self.current_user]
        if current_id in user_df['id'].values:
            current_date = user_df[user_df.id == current_id]['date'].values[0]
            self.logger.info("Current date: {}".format(current_date))
            user_df = user_df[user_df.date < current_date]
        logging.info("User_DF: {}".format(user_df.shape[0]))
        previous = user_df.sort_values('date', ascending=False).head(1).to_dict('records')[0]
        return {
            "is_done": user_df.shape[0] <= 1,
            "sid": previous['id'],
            "data": self.classifier.get_sample_by_id(previous['id']),
            "class": previous['class']
        }

    def skip(self, data):
        self.remaining.remove(data['sid'])
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
