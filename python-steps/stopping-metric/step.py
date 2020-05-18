# This file is the code for the plugin Python step test

import os, json
from dataiku.customstep import *
import dataiku
import numpy as np

from lal import utils
from cardinal import uncertainty


# settings at the step instance level (set by the user creating a scenario step)
step_config = get_step_config()
model = dataiku.Model(step_config['model'])
unlabeled = step_config['unlabeled']
n_samples = int(step_config['n_samples'])

models = sorted(model.list_versions(), key=lambda x:int(x['snippet']['trainDate']))

if len(models) > 1:

    curr_clf = utils.load_classifier(model)
    prev_clf = utils.load_classifier(model, version_id=models[-2]['versionId'])

    unlabeled_df, unlabeled_is_folder = utils.load_data(unlabeled)
    # TODO: select samples that are not part of the training set of the model.
    index = np.random.choice(np.arange(unlabeled_df.shape[0]), size=n_samples)

    preprocessed = utils.preprocess_data(model, unlabeled_df.iloc[index], unlabeled_is_folder, version_id=models[-2]['versionId'])
    prev_preds = np.argmax(uncertainty._get_probability_classes(prev_clf, preprocessed), axis=1)

    preprocessed = utils.preprocess_data(model, unlabeled_df.iloc[index], unlabeled_is_folder)
    curr_preds = np.argmax(uncertainty._get_probability_classes(curr_clf, preprocessed), axis=1)
    
    contradictions = (prev_preds != curr_preds).sum()
    
    variables = dataiku.Project().get_variables()
    standards = variables['standard']
    hist_contradictions = standards.get('_ml_assisted_contradictions', [])
    hist_contradictions.append(contradictions.item())
    standards['_ml_assisted_contradictions'] = hist_contradictions
    variables['standard'] = standards
    dataiku.Project().set_variables(variables)
