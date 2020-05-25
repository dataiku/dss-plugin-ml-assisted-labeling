import logging
from abc import abstractmethod

import pandas as pd

from cardinal.criteria import get_halting_values
from lal import utils


class BaseClassifier(object):
    logger = logging.getLogger(__name__)

    def __init__(self, queries_df, config):
        super(BaseClassifier, self).__init__()
        self.config = None if config is None else self.validate_config(config)
        self.queries_df = queries_df
        self.initial_df = self.get_initial_df()
        self.id_to_index = {}
        self.ordered_ids = list()
        self.df_to_label = self.get_df_to_label()
        for index, row in self.df_to_label.iterrows():
            row_id = self.raw_row_to_id(row)
            self.id_to_index[row_id] = index
            self.ordered_ids.append(row_id)

        if self.is_al_enabled:
            self.halting_values, self.halting_thr_low, self.halting_thr_high = get_halting_values(self.queries_df.sort_values('uncertainty', ascending=True).uncertainty)
            self.halting_values_by_id = dict(zip(self.ordered_ids, self.halting_values))
        else:
            self.halting_values_by_id = None

    @property
    def is_al_enabled(self):
        return self.queries_df is not None and not self.queries_df.empty

    def get_df_to_label(self):
        if self.is_al_enabled:
            logging.info("Taking queries dataframe to label")
            df_to_label = self.queries_df.sort_values('uncertainty', ascending=True)
            df_to_label = df_to_label[self.initial_df.columns]
        else:
            logging.info("Taking initial dataframe to label")
            df_to_label = self.initial_df

        return df_to_label


    def get_session(self):
        return utils.get_current_session_id(self.config.get('queries_ds'))

    def validate_config(self, config):
        self.logger.info("Webapp config: %s" % repr(config))

        if "labels_ds" not in config:
            raise ValueError("Labels dataset not specified. Go to settings tab.")

        return config

    def get_item_by_id(self, sid):
        result = {"raw": self.get_raw_item_by_id(sid)}
        enriched = self.get_enriched_item_by_id(sid)
        if enriched:
            result["enriched"] = enriched
        if self.is_al_enabled:
            result["halting"] = self.halting_values_by_id[sid]
        return result

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

    @staticmethod
    def format_labels_for_stats(raw_labels_series):
        return raw_labels_series
