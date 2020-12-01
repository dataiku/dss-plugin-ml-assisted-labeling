import dataiku
from dataiku.customwebapp import get_webapp_config

from lal.api import define_endpoints
from lal.app_configuration import prepare_datasets
from lal.classifiers.sound_classifier import SoundClassifier
from lal.handlers.dataiku_lal_handler import DataikuLALHandler

config = get_webapp_config()

labels_schema = [
    {"name": "path", "type": "string"}
]
prepare_datasets(config, labels_schema)

unlabeled_mf = dataiku.Folder(config["unlabeled"])
queries_df = dataiku.Dataset(config["queries_ds"]).get_dataframe() if "queries_ds" in config else None
define_endpoints(app, DataikuLALHandler(SoundClassifier(unlabeled_mf, queries_df, config), config))
