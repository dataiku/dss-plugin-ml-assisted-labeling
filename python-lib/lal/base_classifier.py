import logging
from abc import abstractmethod

import numpy as np
import pandas as pd

import dataiku
from dataiku.core import schema_handling
from dataiku.customwebapp import *


class BaseClassifier(object):
    logger = logging.getLogger(__name__)

    @property
    @abstractmethod
    def type(self):
        pass

    def __init__(self):
        super(BaseClassifier, self).__init__()
        self.config = self.read_config()

        self.labels_ds = dataiku.Dataset(self.config["labels_ds"])
        self.labels_df = self.prepare_label_dataset(self.labels_ds)

    def read_config(self):
        config = get_webapp_config()
        self.logger.info("Webapp config: %s" % repr(config))

        if "labels_ds" not in config:
            raise ValueError("Labels dataset not specified. Go to settings tab.")

        return config

    @abstractmethod
    def get_all_sample_ids(self):
        pass

    @abstractmethod
    def get_labeled_sample_ids(self):
        pass

    @abstractmethod
    def get_sample_by_id(self, sid):
        pass

    @property
    @abstractmethod
    def labels_required_schema(self):
        pass

    @property
    def __labels_required_columns(self):
        return {c['name'] for c in self.labels_required_schema}

    def prepare_label_dataset(self, dataset):

        try:
            dataset_schema = dataset.read_schema()
            dataset_schema_columns = {c['name'] for c in dataset_schema}

            if not self.__labels_required_columns.issubset(dataset_schema_columns):
                raise ValueError(
                    "The target dataset should have columns: {}. The provided dataset has columns: {}. "
                    "Please edit the schema in the dataset settings.".format(
                        ', '.join(self.__labels_required_columns), ', '.join(dataset_schema_columns)))

            current_df = dataset.get_dataframe()
        except:
            self.logger.info("{} probably empty".format(dataset.name))
            current_df = pd.DataFrame(columns=self.__labels_required_columns, index=[])
            for col in self.labels_required_schema:
                n = col["name"]
                t = col["type"]
                t = schema_handling.DKU_PANDAS_TYPES_MAP.get(t, np.object_)
                current_df[n] = current_df[n].astype(t)
        return current_df

    @abstractmethod
    def add_label(self, annotaion):
        pass
