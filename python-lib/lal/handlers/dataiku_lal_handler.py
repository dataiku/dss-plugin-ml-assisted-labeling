import logging

import dataiku
from dataiku.customwebapp import get_webapp_config
from lal.handlers.lal_handler import LALHandler

config = get_webapp_config()


class DataikuLALHandler(LALHandler):
    logger = logging.getLogger(__name__)

    meta_ds = dataiku.Dataset(config["metadata_ds"])
    meta_df = meta_ds.get_dataframe()
    labels_ds = dataiku.Dataset(config["labels_ds"])
    labels_df = labels_ds.get_dataframe()

    def __init__(self, classifier, user):
        super().__init__(
            classifier=classifier,
            label_col_name=config['label_col_name'],
            meta_df=DataikuLALHandler.meta_df,
            labels_df=DataikuLALHandler.labels_df,
            user=user
        )

    # Saving should probably be optimized (currently it takes >90% of the response time)
    def save_item_meta(self, new_meta_df, new_meta=None):
        DataikuLALHandler.meta_df = new_meta_df
        self.meta_ds.write_with_schema(new_meta_df)

    def save_item_label(self, new_label_df, new_label=None):
        DataikuLALHandler.labels_df = new_label_df
        self.labels_ds.write_with_schema(new_label_df)
