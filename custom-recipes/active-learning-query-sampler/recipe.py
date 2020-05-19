import logging
import pandas as pd
from pickle import PickleError
from json import JSONDecodeError  
import numpy as np

import dataiku
from dataiku.customrecipe import *

from cardinal import uncertainty
from lal import utils


# Load configuration
config = get_recipe_config()
unlabeled_samples_container = get_input_names_for_role('unlabeled_samples')[0]
unlabeled_test_samples_container = get_input_names_for_role('unlabeled_test')
unlabeled_test_samples_container = unlabeled_test_samples_container[0] if len(unlabeled_test_samples_container) > 0 else None
saved_model_id = get_input_names_for_role('saved_model')[0]
model = dataiku.Model(saved_model_id)
queries_ds = dataiku.Dataset(get_output_names_for_role('queries')[0], ignore_flow=True)

strategy_mapper = {
    'confidence': uncertainty.confidence_sampling,
    'margin': uncertainty.margin_sampling,
    'entropy': uncertainty.entropy_sampling
}

clf = utils.load_classifier(model)

#################
# Active learning

unlabeled_df, unlabeled_is_folder = utils.load_data(unlabeled_samples_container)
X = utils.preprocess_data(model, unlabeled_df, unlabeled_is_folder)
func = strategy_mapper[config['strategy']]
index, uncertainty_scores = func(clf, X=X, n_instances=X.shape[0])
utils.increment_queries_session(queries_ds.short_name)


# Outputs
queries_df = unlabeled_df.loc[index]
queries_df['uncertainty'] = uncertainty_scores
queries_ds.write_with_schema(queries_df)