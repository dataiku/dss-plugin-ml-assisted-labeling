# -*- coding: utf-8 -*-
import os

import pandas as pd, numpy as np
import keras

import dataiku
from dataiku.customrecipe import *
from dataiku import pandasutils as pdu

from cardinal import annotation_aggregator


config = get_recipe_config()

annotations_df = dataiku.Dataset(get_input_names_for_role('annotations_dataset')[0]).get_dataframe()

strategy_mapper = {
    'vote': annotation_aggregator.vote_selection,
    'weighted_vote': None,
    'snorkel': annotation_aggregator.snorkel
}

func = strategy_mapper[config['strategy']]
annotations_df = func(annotations_df)

deduplicated_annotations_dataset = dataiku.Dataset(get_output_names_for_role('deduplicated_annotations_dataset')[0])
deduplicated_annotations_dataset.write_with_schema(annotations_df)