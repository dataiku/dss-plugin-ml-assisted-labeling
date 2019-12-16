# This file is the actual code for the custom Python trigger every-n-annotations

import os, json
import dataiku

from dataiku.customtrigger import *
from dataiku.scenario import Trigger

# the settings of the user for this instance of the trigger
trigger_config = get_trigger_config()

t = Trigger()

annotations_count = trigger_config['annotations_count']
annotations = dataiku.Dataset(trigger_config['dataset'])
annotations_df = annotations.get_dataframe()
stop_annotations = trigger_config['stop_annotations']
stop_annotations_count = trigger_config['stop_annotations_count']
stop_model = trigger_config['stop_model']
stop_model_df = dataiku.Dataset(trigger_config['stop_model_dataset']).get_dataset()
stop_model_column = trigger_config['stop_model_column']
stop_model_epsilon = trigger_config['stop_model_epsilon']
last_session_run = trigger_config['stop_model_epsilon']

trigger = False

# Get session computed from annotations dataset
max_session = annotations_df['session'].max()
n_annotations = (annotations_df['session'] == max_session).sum()
trigger = (max_session > last_session_run and n_annotations >= annotations_count)
if trigger:
    trigger_config['last_session_run'] = max_session

if stop_annotations:
    trigger = (trigger and (annotations_df.shape[0] < stop_annotations_count)) 

if stop_model and stop_model_df.shape[0] >= 2:
    stop_model_df = stop_model_df.sort_values('date')
    metrics = stop_model_df[stop_model_column]
    trigger = (trigger and (np.abz(metrics[-1] - metrics[-2]) > stop_model_epsilon))

if trigger:
    t.fire()