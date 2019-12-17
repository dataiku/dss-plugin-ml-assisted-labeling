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
queries_ds = dataiku.Dataset(get_output_names_for_role('queries')[0], ignore_flow=True)

try:    
    clf = model.get_predictor()._clf
except Exception as e:
    import pickle
    raise pickle.PickleError(ValueError(('\xa0' * 30) + '\xa0\xa0\xa0 'Failed to load the saved model. It is most probably caused by '
                             'discrepencies between the code env used to train the model and the one '
                             'used in the plugin. If not done already, please create an environment '
                             'for your lab running on python 3.6 and using sklearn 0.20 and keras 2.1.5 '
                             '— depending on your model.<br /><br />Original error is {}'.format(e)))
X = model.get_predictor().get_preprocessing().preprocess(unlabeled_df)[0]

strategy_mapper = {
    'confidence': uncertainty.confidence_sampling,
    'margin': uncertainty.margin_sampling,
    'entropy': uncertainty.entropy_sampling
}

current_session = 1
try:
    queries_df = queries_ds.get_dataframe()
    current_session = 1 if queries_df.session.empty else queries_df.session[0] + 1
except Exception as e:
    logging.info("Could not determine session. Default to 1. Original error is: {0}".format(e))

func = strategy_mapper[config['strategy']]
index, uncertainty = func(clf, X=X, n_instances=unlabeled_df.shape[0])
queries_df = unlabeled_df.loc[index]
queries_df['uncertainty'] = uncertainty
queries_df['session'] = current_session

queries_ds.write_with_schema(queries_df)