import dataiku
from dataiku.customwebapp import get_webapp_config
from lal.api import define_endpoints
from lal.app_configuration import prepare_datasets
from lal.classifiers.image_object_classifier import ImageObjectClassifier

config = get_webapp_config()

labels_schema = [
    {"name": "path", "type": "string"}
]
prepare_datasets(labels_schema)

unlabeled_mf = dataiku.Folder(config["unlabeled"])

queries_df = dataiku.Dataset(config["queries_ds"]).get_dataframe() if "queries_ds" in config else None

define_endpoints(app, ImageObjectClassifier(unlabeled_mf, queries_df, config))