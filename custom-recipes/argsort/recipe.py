# -*- coding: utf-8 -*-
import os

import pandas as pd, numpy as np
import keras

import dataiku
from dataiku.customrecipe import *
from dataiku import pandasutils as pdu


config = get_recipe_config()
input_df = dataiku.Dataset(get_input_names_for_role('input_dataset')[0]).get_dataframe()
argsort_column = config['argsort_column']

input_df[argsort_column + '_argsort'] = input_df[argsort_column].rank(method='max')

output_dataset = dataiku.Dataset(get_output_names_for_role('output_dataset')[0])
output_dataset.write_with_schema(input_df)