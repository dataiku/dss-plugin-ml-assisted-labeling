# -*- coding: utf-8 -*-
import os

import pandas as pd, numpy as np

import dataiku
from dataiku.customrecipe import *
from dataiku import pandasutils as pdu

from cardinal import random, density


config = get_recipe_config()

model = dataiku.Model(get_input_names_for_role('saved_model')[0])
unlabeled_df = dataiku.Dataset(get_input_names_for_role('unlabeled_samples')[0]).get_dataframe()
labeled_ds = get_input_names_for_role('labeled_samples')
if len(labeled_ds) > 0:
    # We want the index of labeled samples in the dataset
    labeled_df = dataiku.Dataset(get_input_names_for_role('labeled_samples')[0]).get_dataframe()
    # Select only the columns of the original dataset
    columns = unlabeled_df.columns.values.tolist()
    labeled_df = labeled_df[columns]
    unlabeled_df = unlabeled_df.reset_index()
    idx_labeled = pd.merge(unlabeled_df, labeled_df, on=columns)['index'].values
    unlabeled_df = unlabeled_df[columns]
else:
    idx_labeled = None
                             
X = model.get_predictor().get_preprocessing().preprocess(unlabeled_df)[0]

strategy_mapper = {
    'random': random.random_sampling,
    'density': density.density_sampling
}

func = strategy_mapper[config['strategy']]
index, uncertainty = func(X=X, idx_labeled=idx_labeled, n_instances=unlabeled_df.shape[0])
unlabeled_df = unlabeled_df.loc[index]
unlabeled_df['uncertainty'] = uncertainty

queries = dataiku.Dataset(get_output_names_for_role('queries')[0])
queries.write_with_schema(unlabeled_df)