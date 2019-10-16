import datetime
import json
import logging
from base64 import b64encode

import dataiku
from lal.base_classifier import BaseClassifier


class ImageBboxClassifier(BaseClassifier):
    logger = logging.getLogger(__name__)

    def __init__(self):
        super(ImageBboxClassifier, self).__init__()
        # TODO: move to base class
        self.queries_ds = dataiku.Dataset(self.config['queries_ds'])
        self.queries_df = self.queries_ds.get_dataframe()

        self.control_ds = dataiku.Dataset(self.config["annotations_control"])
        self.control_df = self.prepare_annotation_dataset(self.control_ds)

        self.current_user = dataiku.api_client().get_auth_info()['authIdentifier']

    def add_annotation(self, annotaion):
        path = annotaion.get('sid')
        cat = annotaion.get('category')
        bbox = annotaion.get('bbox')
        comment = annotaion.get('comment')

        bbox = json.loads(bbox)

        for bb in bbox:
            self.annotations_df = self.annotations_df.append({
                'path': path,
                'class': bb['label'],
                'comment': comment,
                'timestamp': datetime.datetime.now(),
                'annotator': self.current_user,
                'x1': bb['left'],
                'y1': bb['top'] + bb['height'],
                'x2': bb['left'] + bb['width'],
                'y2': bb['top']
            }, ignore_index=True)

    def get_all_sample_ids(self):
        user_queries_df = self.queries_df[self.queries_df['annotator'] == self.current_user]
        self.logger.info("All user sample ids count: {}".format(len(user_queries_df)))
        return set(user_queries_df.path)

    def get_labeled_sample_ids(self):
        return set(self.annotations_df[self.annotations_df['annotator'] == self.current_user].path)

    def get_sample_by_id(self, sid):
        self.logger.info('Reading image from: ' + str(sid))
        with self.folder.get_download_stream(sid) as s:
            data = b64encode(s.read())
        bboxes = self.queries_df[self.queries_df['path'] == sid][['x1', 'y1', 'x2', 'y2']].to_dict('records')

        self.logger.info("BBOX: {}".format(bboxes))
        return {"img": data, "bbox": bboxes}

    @property
    def annotations_required_schema(self):
        return [
            {"name": "path", "type": "string"},
            {"name": "annotator", "type": "string"},
            {"name": "x1", "type": "int"},
            {"name": "y1", "type": "int"},
            {"name": "x2", "type": "int"},
            {"name": "y2", "type": "int"},
            {"name": "class", "type": "str"},
            {"name": "timestamp", "type": "int"},
        ]
