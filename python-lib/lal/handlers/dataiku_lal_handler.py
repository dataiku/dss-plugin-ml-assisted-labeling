import logging

import dataiku

from cardinal.criteria import get_stopping_warning
from lal.handlers.lal_handler import LALHandler


class DataikuLALHandler(LALHandler):
    logger = logging.getLogger(__name__)

    def __init__(self, classifier, config):
        self.labels_ds = dataiku.Dataset(config["labels_ds"])
        self.meta_ds = dataiku.Dataset(config["metadata_ds"])
        self.config = config
        super().__init__(
            classifier=classifier,
            label_col_name=config['label_col_name'],
            meta_df=self.meta_ds.get_dataframe(),
            labels_df=self.labels_ds.get_dataframe()
        )

    def get_config(self):
        res = super().get_config()
        res['stopping_messages'] = get_stopping_warning(self.config["metadata_ds"])
        return res

    # Saving should probably be optimized (currently it takes >90% of the response time)
    def save_item_meta(self, new_meta_df, new_meta=None):
        DataikuLALHandler.meta_df = new_meta_df
        self.meta_ds.write_with_schema(new_meta_df)

    def save_item_label(self, new_label_df, new_label=None):
        DataikuLALHandler.labels_df = new_label_df
        self.labels_ds.write_with_schema(new_label_df)
