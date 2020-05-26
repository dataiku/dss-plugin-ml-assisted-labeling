# This file is the code for the plugin Python step test

import dataiku
import numpy as np
from dataiku.customstep import *

from cardinal import uncertainty
from lal import utils
# settings at the step instance level (set by the user creating a scenario step)
from lal.classifiers.base_classifier import FolderBasedDataClassifier, TableBasedDataClassifier

step_config = get_step_config()
model = dataiku.Model(step_config['model'])
unlabeled = step_config['unlabeled']
metadata = step_config['metadata']
n_samples = int(step_config['n_samples'])

versions = sorted(model.list_versions(), key=lambda x:int(x['snippet']['trainDate']), reverse=True)

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

compare_with_version = 0
ref_n_samples = versions[0]['snippet']['trainInfo']['trainRows']
while compare_with_version < len(versions) - 1:
    compare_with_version += 1
    n_samples_i = versions[compare_with_version]['snippet']['trainInfo']['trainRows']
    if ref_n_samples - n_samples_i >= 20:
        break

if versions[0]['snippet']['trainInfo']['trainRows'] - versions[compare_with_version]['snippet']['trainInfo']['trainRows'] < 20:
    # Not enough samples to trigger computation
    exit()

prev_version_id = versions[compare_with_version]['versionId']

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

utils.add_perf_metrics(metadata, contradictions.item(), auc)