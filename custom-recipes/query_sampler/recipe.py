# -*- coding: utf-8 -*-
import os

import pandas as pd, numpy as np
import keras

import dataiku
from dataiku.customrecipe import *
from dataiku import pandasutils as pdu

from cardinal import uncertainty, dss_utils


config = get_recipe_config()

unlabeled_df = dataiku.Dataset(get_input_names_for_role('unlabeled_samples')[0]).get_dataframe()

model = dataiku.Model(get_input_names_for_role('saved_model')[0])
clf = model.get_predictor()._clf
X = model.get_predictor().get_preprocessing().preprocess(unlabeled_df)[0]

strategy_mapper = {
    'uncertainty': uncertainty.uncertainty_sampling,
    'margin': uncertainty.margin_sampling,
    'entropy': uncertainty.entropy_sampling
}

func = strategy_mapper[config['strategy']]
index, uncertainty = func(clf, X=X, n_instances=unlabeled_df.shape[0])
unlabeled_df = unlabeled_df.loc[index]
# TODO: margin is not an uncertainty score. We should either convert it or rename this column
unlabeled_df['uncertainty'] = uncertainty

queries = dataiku.Dataset(get_output_names_for_role('queries')[0])
queries.write_with_schema(unlabeled_df)