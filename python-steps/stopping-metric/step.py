# This file is the code for the plugin Python step test

import logging

import dataiku
import numpy as np
from dataiku.customstep import *

from cardinal import uncertainty
from lal import utils
# settings at the step instance level (set by the user creating a scenario step)
from lal.classifiers.base_classifier import FolderBasedDataClassifier, TableBasedDataClassifier

logging.basicConfig(level=logging.INFO, format='%(name)s %(levelname)s - %(message)s')

step_config = get_step_config()
model = dataiku.Model(step_config['model'])
unlabeled = step_config['unlabeled']
metadata = step_config['metadata']
n_samples = int(step_config['n_samples'])

versions = sorted(model.list_versions(), key=lambda x: int(x['snippet']['trainDate']), reverse=True)

if len(versions) < 2:
    exit()

curr_clf = utils.load_classifier(model)

# We do not want to look at the difference if 20 samples have not been sampled
# For example, if the number of labeled samples per model is:
# [1, 8, 21, 29, 42, 54]
#  ^  ^  ^   ^   ^
#  A  a  B   b   C
# Then we want to compare B against A, and C against B but not b against a:
# even if there is a difference of 20, a is considered ignored because it is
# too close to A.

curr_n_samples = versions[0]['snippet']['trainInfo']['trainRows']
historical_metrics = utils.get_perf_metrics(metadata)
if len(historical_metrics) != 0:
    last_metrics = sorted(historical_metrics, key=lambda x: int(x['n_samples']), reverse=True)[0]

    samples_delta = curr_n_samples - last_metrics['n_samples']
    if samples_delta < 20:
        logging.info("Not enough newly labeled samples since the last model evaluation, required at least 20, obtained: {}".format(samples_delta))
        # Not enough samples to trigger computation
        exit()
    prev_version_id = last_metrics['versionId']
else:
    prev_version_id = versions[-1]['versionId']

# To compute contradictions, select samples that are not labeled in the latest model
unlabeled_df, unlabeled_is_folder = utils.load_data(unlabeled)
labeled_ids = set(dataiku.Dataset(metadata).get_dataframe()['data_id'])
validation_ids = []
for index, row in unlabeled_df.sample(frac=1).iterrows():
    # get the id of the sample
    if unlabeled_is_folder:
        sid = FolderBasedDataClassifier.raw_row_to_id(row)
    else:
        sid = TableBasedDataClassifier.raw_row_to_id(row)
    if not sid in labeled_ids:
        labeled_ids.add(sid)
        validation_ids.append(index)
        if len(validation_ids) == n_samples:
            break
index = np.asarray(validation_ids)

prev_clf = utils.load_classifier(model, prev_version_id)
preprocessed = utils.preprocess_data(model, unlabeled_df.iloc[index], unlabeled_is_folder, version_id=prev_version_id)
prev_preds = np.argmax(uncertainty._get_probability_classes(prev_clf, preprocessed), axis=1)
preprocessed = utils.preprocess_data(model, unlabeled_df.iloc[index], unlabeled_is_folder)
curr_preds = np.argmax(uncertainty._get_probability_classes(curr_clf, preprocessed), axis=1)

contradictions = (prev_preds != curr_preds).sum() / n_samples
auc = versions[0]['snippet']['auc']

utils.add_perf_metrics(metadata, versions[0]['versionId'], curr_n_samples, contradictions.item(), auc)
