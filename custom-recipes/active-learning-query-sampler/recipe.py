import logging

import pandas as pd

import dataiku
from cardinal import uncertainty
from dataiku.customrecipe import *

config = get_recipe_config()
unlabeled_samples_container = get_input_names_for_role('unlabeled_samples')[0]
logging.info("Reading unlabeled samples from {0}".format(unlabeled_samples_container))
try:
    unlabeled_df = pd.DataFrame(dataiku.Dataset(unlabeled_samples_container).get_dataframe())
    logging.info("Unlabeled input is a dataset")
except Exception as e:
    logging.info("Unlabeled input is a folder: {0}".format(e))
    unlabeled_samples = dataiku.Folder(unlabeled_samples_container)
    unlabeled_df = pd.DataFrame(unlabeled_samples.list_paths_in_partition(), columns=["path"])

model = dataiku.Model(get_input_names_for_role('saved_model')[0])

clf = model.get_predictor()._clf
X = model.get_predictor().get_preprocessing().preprocess(unlabeled_df)[0]

strategy_mapper = {
    'confidence': uncertainty.confidence_sampling,
    'margin': uncertainty.margin_sampling,
    'entropy': uncertainty.entropy_sampling
}

func = strategy_mapper[config['strategy']]
index, uncertainty = func(clf, X=X, n_instances=unlabeled_df.shape[0])
unlabeled_df = unlabeled_df.loc[index]
unlabeled_df['uncertainty'] = uncertainty

queries = dataiku.Dataset(get_output_names_for_role('queries')[0])
queries.write_with_schema(unlabeled_df)

# Increase session ID
session_var = "labelling-and-active-learning_session"
dataiku.get_custom_variables()[session_var] = dataiku.get_custom_variables().get(session_var, 0) + 1