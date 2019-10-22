import logging
from base64 import b64encode

import dataiku
from lal.base_classifier import BaseClassifier


class ImageClassifier(BaseClassifier):
    logger = logging.getLogger(__name__)

    def __init__(self):
        super(ImageClassifier, self).__init__()
        self.folder = dataiku.Folder(self.config["folder"])
        self.current_user = dataiku.api_client().get_auth_info()['authIdentifier']

    def add_annotation(self, annotaion):
        sid = annotaion.get('sid')
        cat = annotaion.get('category')
        # comment = annotaion.get('comment')
        comment = annotaion.get('points')

        self.annotations_df = self.annotations_df.append({
            'id': sid,
            'class': cat,
            'comment': comment,
            'session': 0,
            'annotator': self.current_user,
        }, ignore_index=True)

    @property
    def annotations_required_schema(self):
        # TODO: Named tuple?
        return [{"name": "id", "type": "string"},
                {"name": "class", "type": "string"},
                {"name": "comment", "type": "string"},
                {"name": "session", "type": "int"},
                {"name": "annotator", "type": "string"}]

    def get_sample_by_id(self, sid):
        self.logger.info('Reading image from: ' + str(sid))
        with self.folder.get_download_stream(sid) as s:
            data = b64encode(s.read())
            
        self.logger.info("Read: {0}, {1}".format(len(data), type(data)))
        return data.decode('utf-8')

    def get_all_sample_ids(self):
        return set(self.folder.list_paths_in_partition())

    def get_labeled_sample_ids(self):
        return set(self.annotations_df.loc[self.annotations_df['annotator'] == self.current_user]['id'])
