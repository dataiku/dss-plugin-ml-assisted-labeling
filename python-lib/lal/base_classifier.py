import logging
from abc import abstractmethod

import numpy as np
import pandas as pd

import dataiku
from dataiku.core import schema_handling
from dataiku.customwebapp import *


class BaseClassifier(object):
    logger = logging.getLogger(__name__)

    def __init__(self):
        super(BaseClassifier, self).__init__()
        self.config = self.read_config()

        self.annotations_ds = dataiku.Dataset(self.config["annotations_ds"])
        self.annotations_df = self.prepare_annotation_dataset(self.annotations_ds)

    def read_config(self):
        config = get_webapp_config()
        self.logger.info("Webapp config: %s" % repr(config))

        if "folder" not in config:
            raise ValueError("Image folder not specified. Go to settings tab.")
        if "annotations_ds" not in config:
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
    def annotations_required_schema(self):
        pass

    @property
    def __annotations_required_columns(self):
        return {c['name'] for c in self.annotations_required_schema}

    def prepare_annotation_dataset(self, dataset):

        try:
            dataset_schema = dataset.read_schema()
            dataset_schema_columns = {c['name'] for c in dataset_schema}

            if not self.__annotations_required_columns.issubset(dataset_schema_columns):
                raise ValueError(
                    "The target dataset should have columns: {}. The provided dataset has columns: {}. "
                    "Please edit the schema in the dataset settings.".format(
                        ', '.join(self.__annotations_required_columns), ', '.join(dataset_schema_columns)))

            current_df = dataset.get_dataframe()
        except:
            self.logger.info("{} probably empty".format(dataset.name))
            current_df = pd.DataFrame(columns=self.__annotations_required_columns, index=[])
            for col in self.annotations_required_schema:
                n = col["name"]
                t = col["type"]
                t = schema_handling.DKU_PANDAS_TYPES_MAP.get(t, np.object_)
                current_df[n] = current_df[n].astype(t)
        return current_df

    @abstractmethod
    def add_annotation(self, annotaion):
        pass
