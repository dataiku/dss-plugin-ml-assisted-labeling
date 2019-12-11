import dataiku
from dataiku.customwebapp import get_webapp_config
from lal.api import define_endpoints
from lal.app_configuration import prepare_datasets

from lal.classifiers.tabular_classifier import TabularClassifier

config = get_webapp_config()
prepare_datasets()
initial_df = dataiku.Dataset(config["unlabeled"]).get_dataframe()
queries_df = dataiku.Dataset(config["queries_ds"]).get_dataframe() if "queries_ds" in config else None

define_endpoints(app, TabularClassifier(initial_df, queries_df, config))
