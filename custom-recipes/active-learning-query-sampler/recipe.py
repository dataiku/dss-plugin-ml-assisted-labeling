import logging
import pandas as pd
from pickle import PickleError

import dataiku
from dataiku.customrecipe import *

from cardinal import uncertainty
from dss_utils import get_input_full_name


# Load configuration
config = get_recipe_config()
unlabeled_samples_container = get_input_names_for_role('unlabeled_samples')[0]  # get_input_full_name('unlabeled_samples')
saved_model_id = get_input_names_for_role('saved_model')[0]
model = dataiku.Model(saved_model_id)
queries_ds = dataiku.Dataset(get_output_names_for_role('queries')[0], ignore_flow=True)

strategy_mapper = {
    'confidence': uncertainty.confidence_sampling,
    'margin': uncertainty.margin_sampling,
    'entropy': uncertainty.entropy_sampling
}

# Helper functions
def prettify_error(s):
    """Adds a blank and replaces regular spaces by non-breaking in the first 90 characters
    
    This function adds a big blank space and forces the first words to be a big block of
    unbreakable words. This enforces a newline in the DSS display and makes the error prettier.
    """
    return '\xa0' * 130 + ' \n' + s[:90].replace(' ', '\xa0') + s[90:]

# DSS entities loading
logging.info("Reading unlabeled samples from {0}".format(unlabeled_samples_container))
try:
    unlabeled_df = pd.DataFrame(dataiku.Dataset(unlabeled_samples_container).get_dataframe())
    logging.info("Unlabeled input is a dataset")
except Exception as e:
    logging.info("Unlabeled input is a folder: {0}".format(e))
    print('DEBUG', unlabeled_samples_container)
    unlabeled_samples = dataiku.Folder(unlabeled_samples_container)
    unlabeled_df = pd.DataFrame(unlabeled_samples.list_paths_in_partition(), columns=["path"])

logging.info("Trying to load model from {0}".format(saved_model_id))
try:
    clf = model.get_predictor()._clf
except Exception as e:
    raise PickleError(
        prettify_error('Failed to load the saved model. The visual Machine Learning '
                       'code environment needs to be compatible with the code environment of this plugin.' ) +
        prettify_error('Original error is {}'.format(e)))

# Find the current session from the previous iteration of queries
current_session = 1
try:
    queries_df = queries_ds.get_dataframe()
    current_session = 1 if queries_df.session.empty else queries_df.session[0] + 1
except Exception as e:
    logging.info("Could not determine session. Default to 1. Original error is: {0}".format(e))

# Active learning
func = strategy_mapper[config['strategy']]
print('DEBUG', unlabeled_df)
X = model.get_predictor().get_preprocessing().preprocess(unlabeled_df)[0]
print('DEBUG', X)
index, uncertainty = func(clf, X=X, n_instances=unlabeled_df.shape[0])

# Outputs
queries_df = unlabeled_df.loc[index]
queries_df['uncertainty'] = uncertainty
queries_df['session'] = current_session
queries_ds.write_with_schema(queries_df)