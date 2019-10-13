import logging

from dataiku.customwebapp import *
from lal.image_classificator import ImageClassifier
import dataiku
import json


class LALHandler(object):
    logger = logging.getLogger(__name__)

    def __init__(self):
        super(LALHandler, self).__init__()
        self.config = get_webapp_config()
        self.current_user = dataiku.api_client().get_auth_info()['authIdentifier']

        self.lal_app = ImageClassifier()

        self.remaining = self.get_remaining_queries()

    def get_remaining_queries(self):
        # try:
        #     self.logger.info("Trying to sort queries by uncertainty")
        #     queries = dataiku.Dataset(self.config["query_dataset"]).get_dataframe()['path'].sort_values('uncertainty')
        #     remaining = queries.loc[queries.apply(lambda x: x not in self.labelled)].values.tolist()
        #     # We use pop to get samples from this list so we need to reverse the order
        #     return remaining[::-1]
        # except:
        # self.logger.info("Not taking into account uncertainty, serving random queries")
        return self.lal_app.get_all_sample_ids() - self.lal_app.get_labeled_sample_ids()

    def get_sample(self):
        if len(self.remaining) > 0:
            sid = self.remaining.pop()
        else:
            sid = None
        total_count = len(self.lal_app.get_all_sample_ids())
        # -1 because the current is not counted :
        skipped_count = len(self.lal_app.get_all_sample_ids()) - len(self.lal_app.get_labeled_sample_ids()) - len(
            self.remaining) - 1
        labelled_count = len(self.lal_app.get_labeled_sample_ids())
        by_category = self.lal_app.annotations_df['class'].value_counts().to_dict()

        return {
            "sid": sid,
            "data": self.lal_app.get_sample_by_id(sid),
            "labelled": labelled_count,
            "total": total_count,
            "skipped": skipped_count,
            "byCategory": by_category
        }

    def classify(self, data):
        self.logger.info("Classifying: %s" % json.dumps(data))

        sid = data.get('sid')
        cat = data.get('category')
        # comment = data.get('comment')
        comment = data.get('points')

        self.lal_app.annotations_df = self.lal_app.annotations_df.append({
            'id': sid,
            'class': cat,
            'comment': comment,
            'session': 0,
            'annotator': self.lal_app.current_user,
        }, ignore_index=True)
        self.lal_app.labels_ds.write_with_schema(self.lal_app.annotations_df)
        self.logger.info("Wrote labels_df:  %s" % str(self.lal_app.annotations_df.shape))

        self.lal_app.get_labeled_sample_ids().add(sid)
        return self.get_sample()
