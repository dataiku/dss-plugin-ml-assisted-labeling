import logging
from abc import abstractmethod

import pandas as pd


class BaseClassifier(object):
    logger = logging.getLogger(__name__)

    def __init__(self, queries_df, config):
        super(BaseClassifier, self).__init__()
        self.config = None if config is None else self.validate_config(config)
        self.queries_df = queries_df
        self.initial_df = self.get_initial_df()
        self.id_to_index = {}
        self.ordered_ids = list()
        for index, row in self.df_to_label.iterrows():
            row_id = self.raw_row_to_id(row)
            self.id_to_index[row_id] = index
            self.ordered_ids.append(row_id)

    @property
    def is_al_enabled(self):
        return self.queries_df is not None and not self.queries_df.empty

    @property
    def df_to_label(self):
        if self.is_al_enabled:
            logging.info("Taking queries dataframe to label")
            df_to_label = self.queries_df.sort_values('uncertainty', ascending=True)
            df_to_label = df_to_label[self.initial_df.columns]
        else:
            logging.info("Taking initial dataframe to label")
            df_to_label = self.initial_df

        return df_to_label

    def get_session(self):
        if self.queries_df is None or self.queries_df.empty:
            return 0
        return self.queries_df.session[0]  # all session values are the same in queries, taking first

    def validate_config(self, config):
        self.logger.info("Webapp config: %s" % repr(config))

        if "labels_ds" not in config:
            raise ValueError("Labels dataset not specified. Go to settings tab.")

        return config

    def get_item_by_id(self, sid):
        return {"raw": self.get_raw_item_by_id(sid),
                "enriched": self.get_enriched_item_by_id(sid)}

    def get_enriched_item_by_id(self, sid):
        pass

    def get_raw_item_by_id(self, data_id):
        df = self.df_to_label.where((pd.notnull(self.df_to_label)), None).astype('object')
        return df.loc[self.id_to_index[data_id]].to_dict()

    def serialize_label(self, label):
        return str(label[0])

    def deserialize_label(self, label):
        return [label]

    @abstractmethod
    def raw_row_to_id(self, raw):
        pass

    def get_all_item_ids_list(self):
        return self.ordered_ids

    @abstractmethod
    def get_initial_df(self):
        pass

    @property
    @abstractmethod
    def type(self):
        pass
