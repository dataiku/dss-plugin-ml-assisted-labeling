import logging

import numpy as np
import pandas as pd

import dataiku
from dataiku.core import schema_handling
from dataiku.customwebapp import *


class ImageClassificator(object):
    required_schema = [{"name": "path", "type": "string"},
                       {"name": "class", "type": "string"},
                       {"name": "comment", "type": "string"},
                       {"name": "session", "type": "int"},
                       {"name": "annotator", "type": "string"}]
    logger = logging.getLogger(__name__)

    def __init__(self):
        super(ImageClassificator, self).__init__()

        self.config = self.read_config()

        self.current_schema = None
        self.current_schema_columns = None
        self.remaining = None
        self.current_df = None

        self.current_user = dataiku.api_client().get_auth_info()['authIdentifier']
        self.dataset = dataiku.Dataset(self.config["dataset"])
        self.folder = dataiku.Folder(self.config["folder"])

        self.init_schema()
        self.validate_schema()
        self.init_current_df()

        self.labelled = set(self.current_df.loc[self.current_df['annotator'] == self.current_user]['path'])
        self.all_paths = set(self.folder.list_paths_in_partition())
        self.remaining = self.get_remaining_queries()

    def read_config(self):
        config = get_webapp_config()
        self.logger.info("Webapp config: %s" % repr(config))

        if "folder" not in config:
            raise ValueError("Image folder not specified. Go to settings tab.")
        if "dataset" not in config:
            raise ValueError("Output dataset not specified. Go to settings tab.")
        if "query_dataset" not in config:
            raise ValueError("Queries dataset not specified. Go to settings tab.")

        return config

    def init_schema(self):
        self.dataset.write_schema(self.required_schema)
        try:
            self.current_schema = self.dataset.read_schema()
        except:
            self.dataset.write_schema(self.required_schema)

        # TODO : What's going on here? Why writing schema 2 times?

        self.current_schema_columns = [c['name'] for c in self.current_schema]

    def validate_schema(self):
        required_columns = [c['name'] for c in self.required_schema]

        if not set(required_columns).issubset(set(self.current_schema_columns)):
            raise ValueError(
                "The target dataset should have columns: {}. The provided dataset has columns: {}. Please edit the schema in the dataset settings.".format(
                    ', '.join(required_columns), ', '.join(self.current_schema_columns)))

    def init_current_df(self):
        try:
            self.current_df = self.dataset.get_dataframe()
        except:
            self.logger.info("Dataset probably empty")
            self.current_df = pd.DataFrame(columns=self.current_schema_columns, index=[])
            for col in self.current_schema:
                n = col["name"]
                t = col["type"]
                t = schema_handling.DKU_PANDAS_TYPES_MAP.get(t, np.object_)
                self.current_df[n] = self.current_df[n].astype(t)

    def get_remaining_queries(self):
        try:
            self.logger.info("Trying to sort queries by uncertainty")
            queries = dataiku.Dataset(self.config["query_dataset"]).get_dataframe()['path'].sort_values('uncertainty')
            remaining = queries.loc[queries.apply(lambda x: x not in self.labelled)].values.tolist()
            # We use pop to get samples from this list so we need to reverse the order
            return remaining[::-1]
        except:
            self.logger.info("Not taking into account uncertainty, serving random queries")
            return self.all_paths - self.labelled
