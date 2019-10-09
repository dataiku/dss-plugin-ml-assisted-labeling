import logging
from base64 import b64encode

from dataiku.customwebapp import *
from lal.image_classificator import ImageClassificator
import dataiku


class LALHandler(object):
    logger = logging.getLogger(__name__)

    def __init__(self):
        super(LALHandler, self).__init__()
        self.config = get_webapp_config()

        self.lal_app = ImageClassificator()

    def get_sample(self):
        if len(self.lal_app.remaining) > 0:
            next_path = self.lal_app.remaining.pop()
        else:
            next_path = None
        total_count = len(self.lal_app.all_paths)
        skipped_count = len(self.lal_app.all_paths) - len(self.lal_app.labelled) - len(
            self.lal_app.remaining) - 1  # -1 because the current is not counted
        labelled_count = len(self.lal_app.labelled)
        by_category = self.lal_app.annotations_df['class'].value_counts().to_dict()

        return {"nextPath": next_path,
                "labelled": labelled_count,
                "total": total_count,
                "skipped": skipped_count,
                "byCategory": by_category}

    def classify(self, data):
        self.logger.info("Classifying: %s" % json.dumps(data))

        path = data.get('path')
        cat = data.get('category')
        # comment = data.get('comment')
        comment = data.get('points')

        current_df = self.lal_app.annotations_df.append({
            'path': path,
            'class': cat,
            'comment': comment,
            'session': 0,
            'annotator': self.lal_app.current_user,
        }, ignore_index=True)
        self.lal_app.labels_ds.write_with_schema(current_df)
        self.lal_app.labelled.add(path)
        return self.get_sample()

    def get_image(self, path):
        self.logger.info('path: ' + str(path))
        with self.lal_app.folder.get_download_stream(path) as s:
            data = b64encode(s.read())
        return {"data": data}
