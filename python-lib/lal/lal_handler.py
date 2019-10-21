import logging

import dataiku
from dataiku.customwebapp import *
import json

class LALHandler(object):
    logger = logging.getLogger(__name__)

    def __init__(self, classifier):
        """

        :type classifier: lal.base_classifier.BaseClassifier
        """
        super(LALHandler, self).__init__()
        self.config = get_webapp_config()
        self.current_user = dataiku.api_client().get_auth_info()['authIdentifier']

        self.classifier = classifier

        self.remaining = self.get_remaining_queries()

    def get_remaining_queries(self):
        try:
            self.logger.info("Trying to sort queries by uncertainty")
            queries_df = dataiku.Dataset(self.config["queries_ds"]).get_dataframe()
            queries_df = queries_df.sort_values('uncertainty', ascending=False)['id']
            return set(queries_df.tolist()) - self.classifier.get_labeled_sample_ids()
        except:
            self.logger.info("Not taking into account uncertainty, serving random queries")
            return self.classifier.get_all_sample_ids() - self.classifier.get_labeled_sample_ids()

    def get_sample(self):
        self.logger.info("Getting sample")
        if self.is_stopping_criteria_met():
            return {
                "is_done": True
            }
        if len(self.remaining) > 0:
            sid = self.remaining.pop()
        else:
            sid = None
        total_count = len(self.classifier.get_all_sample_ids())
        # -1 because the current is not counted :
        labelled_count = len(self.classifier.get_labeled_sample_ids())
        skipped_count = total_count - labelled_count - len(self.remaining) - 1
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

        self.classifier.annotations_ds.write_with_schema(self.classifier.annotations_df)
        self.logger.info("Wrote Annotations Dataframe of shape:  %s" % str(self.classifier.annotations_df.shape))

        return self.get_sample()

    def is_stopping_criteria_met(self):
        return len(self.remaining) < 0
