import logging

import numpy as np
import pandas as pd

import dataiku
from dataiku.core import schema_handling


metadata_required_schema_base = [
    {"name": "date", "type": "date"},
    {"name": "data_id", "type": "string"},
    {"name": "comment", "type": "string"},
    {"name": "session", "type": "int"},
    {"name": "status", "type": "string"},
    {"name": "annotator", "type": "string"}
]


def prepare_datasets(config, unlabeled_schema=None):
    logging.info("Preparing datasets if needed")
    unlabeled_schema = unlabeled_schema or dataiku.Dataset(config["unlabeled"]).read_schema()

    lbl_col = config.get('label_col_name')
    lbl_id_col = "{}_id".format(lbl_col)

    schema_extra = [{"name": lbl_col, 'type': 'string'}, {"name": lbl_id_col, 'type': 'int'}]

    metadata_required_schema = metadata_required_schema_base + schema_extra
    labels_schema = unlabeled_schema + schema_extra

    prepare_dataset(labels_schema, dataiku.Dataset(config['labels_ds']))

    if 'queries_ds' in config:
        queries_schema = unlabeled_schema + [{"name": "uncertainty", "type": "float"}]
        prepare_dataset(queries_schema, dataiku.Dataset(config['queries_ds']))

    prepare_dataset(metadata_required_schema, dataiku.Dataset(config['metadata_ds']))


def prepare_dataset(required_schema, dataset):
    logging.info("Preparing dataset: {0}".format(dataset.name))
    required_cols = {c['name'] for c in required_schema}
    try:
        _ = dataset.read_metadata()
    except Exception as e:
        raise ValueError("Dataset {} does not exist (Original error: {e}".format(dataset.name, e))

    try:
        ds_cols = {c['name'] for c in dataset.read_schema()}
    except Exception as e:
        logging.info("Dataset has no schema, will create it.")
        ds_cols = set()

    
    if len(ds_cols) == 0:
        logging.info("Dataset is empty, creating the schema")
        current_df = pd.DataFrame(columns=required_cols, index=[])
        for col in required_schema:
            pandas_type = schema_handling.DKU_PANDAS_TYPES_MAP.get(col["type"], np.object_)
            current_df[col["name"]] = current_df[col["name"]].astype(pandas_type)
        logging.info("Writing schema: {0} for {1}".format(current_df.columns, dataset.name))
        dataset.write_with_schema(current_df)
    elif len(ds_cols) > 0 and required_cols.issubset(ds_cols):
        logging.info("Dataset is not empty but has the right schema. Skipping schema creation")
    else:
        raise ValueError(
            "The target dataset should be empty or have columns: {}. The provided dataset has columns: {}. "
            "Please edit the schema in the dataset settings or create a new dataset.".format(
                ', '.join(required_cols), ', '.join(ds_cols)))
    logging.info("Done preparing {0}".format(dataset.name))
