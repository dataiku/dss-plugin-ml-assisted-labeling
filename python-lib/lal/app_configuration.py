import logging

import numpy as np
import pandas as pd

import dataiku
from dataiku.core import schema_handling
from dataiku.customwebapp import get_webapp_config

config = get_webapp_config()

lbl_col = config['label_col_name']
lbl_id_col = config['label_col_name'] + "_id"

metadata_required_schema = [
    {"name": "date", "type": "date"},
    {"name": "data_id", "type": "string"},
    {"name": lbl_col, "type": "string"},
    {"name": lbl_id_col, "type": "string"},
    {"name": "comment", "type": "string"},
    {"name": "session", "type": "int"},
    {"name": "status", "type": "string"},
    {"name": "annotator", "type": "string"}
]


def prepare_datasets(unlabeled_schema=None):
    logging.info("Preparing datasets if needed")
    unlabeled_schema = unlabeled_schema or dataiku.Dataset(config["unlabeled"]).read_schema()

    labels_schema = unlabeled_schema + [{"name": config['label_col_name'], 'type': 'string'},
                                        {"name": config['label_col_name'] + "_id", 'type': 'string'}]

    prepare_dataset(labels_schema, dataiku.Dataset(config['labels_ds']))

    if 'queries_ds' in config:
        queries_schema = unlabeled_schema + [{"name": "uncertainty", "type": "float"}, {"name": "session", "type": "int"}]
        prepare_dataset(queries_schema, dataiku.Dataset(config['queries_ds']))

    prepare_dataset(metadata_required_schema, dataiku.Dataset(config['metadata_ds']))


def prepare_dataset(required_schema, dataset):
    logging.info("Preparing dataset: {0}".format(dataset.name))
    required_cols = {c['name'] for c in required_schema}
    try:
        df = dataset.get_dataframe()
        if not required_cols.issubset(df.columns):
            raise ValueError(
                "The target dataset should have columns: {}. The provided dataset has columns: {}. "
                "Please edit the schema in the dataset settings.".format(
                    ', '.join(required_cols), ', '.join(dataset.cols)))
    except Exception as e:
        logging.info("{0} probably empty: {1}".format(dataset.name, e))
        current_df = pd.DataFrame(columns=required_cols, index=[])
        for col in required_schema:
            n = col["name"]
            t = col["type"]
            t = schema_handling.DKU_PANDAS_TYPES_MAP.get(t, np.object_)
            current_df[n] = current_df[n].astype(t)
        logging.info("Writing schema: {0} for {1}".format(current_df.columns, dataset.name))
        dataset.write_with_schema(current_df)
    logging.info("Done preparing {0}".format(dataset.name))
