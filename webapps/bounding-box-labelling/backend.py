from dataiku.customwebapp import *

import dataiku
from dataiku.core import schema_handling
from flask import request
from base64 import b64encode
import pandas as pd
import numpy as np
import datetime
import time
import json


# CONFIGURATION

if "folder" not in get_webapp_config():
    raise ValueError("Input folder not specified. Go to settings tab.")

if "annotations" not in get_webapp_config():
    raise ValueError("Output dataset not specified. Go to settings tab.")

if "queries" not in get_webapp_config():
    raise ValueError("Input queries not specified. Go to settings tab.")
    
config = get_webapp_config()


# DATA LOADING

folder_id = config["folder"]
folder = dataiku.Folder(folder_id)

queries_name = config['queries']
queries = dataiku.Dataset(queries_name)
queries_df = queries.get_dataframe()

annotations_name = config["annotations"]
annotations = dataiku.Dataset(annotations_name)

control_name = config["annotations_control"]
control = dataiku.Dataset(control_name)

annotations_required_schema = [
    {"name":"path", "type":"string"},
    {"name":"annotator", "type":"string"},
    {"name":"x1", "type":"int"},
    {"name":"y1", "type":"int"},
    {"name":"x2", "type":"int"},
    {"name":"y2", "type":"int"},
    {"name":"class_name", "type":"str"},
    {"name":"timestamp", "type":"int"},
]

# Check that the schema is the one expected
annotations_required_columns = [c['name'] for c in annotations_required_schema]


def prepare_annotation_dataset(dataset):
    
    try:
        dataset_schema = dataset.read_schema()
        dataset_schema_columns = [c['name'] for c in dataset_schema]
    
        if not set(annotations_required_columns).issubset(set(dataset_schema_columns)):
            raise ValueError("The target dataset should have columns: {}. The provided dataset has columns: {}. Please edit the schema in the dataset settings.".format(', '.join(annotations_required_columns), ', '.join(annotations_schema_columns)))

        current_df = dataset.get_dataframe()
    except:
        print("Annotations probably empty")
        current_df = pd.DataFrame(columns=annotations_required_columns, index=[])
        for col in annotations_required_schema:
            n = col["name"]
            t = col["type"]
            t = schema_handling.DKU_PANDAS_TYPES_MAP.get(t, np.object_)
            current_df[n] = current_df[n].astype(t)
    return current_df

annotations_df = prepare_annotation_dataset(annotations)
control_df = prepare_annotation_dataset(control)


# FETCHING OF QUERIES FOR ANNOTATIONS

# Identify the annotator
current_user = dataiku.api_client().get_auth_info()['authIdentifier']    
user_queries_df = queries_df[queries_df['annotator'] == current_user]


# ENDPOINTS

@app.route('/get-image-base64')
def get_image():
    path = request.args.get('path')
    print('path: ' + str(path))
    with folder.get_download_stream(path) as s:
        data = b64encode(s.read())
    return json.dumps({"data": data})

@app.route('/next')
def next():
    global user_queries_df
    bbox = None
    if queries_df.shape[0] > 0:
        path = user_queries_df.iloc[0].path
        bbox = []
        for _, row in user_queries_df[user_queries_df.path == path].iterrows():
            if row.x1:
                bbox.append(dict(
                    x1 = row.x1,
                    y1 = row.y1,
                    x2 = row.x2,
                    y2 = row.y2
                ))
            next_path = queries_df.iloc[0]['path']
    else:
        next_path = None
    return json.dumps({"nextPath": next_path, "bbox": bbox, "remaining": len(queries_df.path.unique())}) 

@app.route('/classify')
def classify():
    global queries_df, user_queries_df, annotations_df, control_df, current_user, annotations, control
    path = request.args.get('path')
    cat = request.args.get('category')
    bbox = request.args.get('bbox')
    comment = request.args.get('comment')

    # Remove query from queries df
    query_type = user_queries_df[((user_queries_df['annotator'] == current_user) & (user_queries_df['path'] == path))].iloc[0].type
    queries_df = queries_df[~((queries_df['annotator'] == current_user) & (queries_df['path'] == path))]
    user_queries_df = user_queries_df[~((user_queries_df['annotator'] == current_user) & (user_queries_df['path'] == path))]
    
    bbox = json.loads(bbox)
    target_db = annotations if query_type == 'query' else control
    target_df = annotations_df if query_type == 'query' else control_df
    
    for bb in bbox:
        target_df = target_df.append({
            'path': path,
            'class_name': bb['label'],
            # 'comment': comment,
            'timestamp': datetime.datetime.now(),
            'annotator': current_user,
            'x1': bb['left'],
            'y1': bb['top'] + bb['height'],
            'x2': bb['left'] + bb['width'],
            'y2': bb['top']
        }, ignore_index=True)
    target_db.write_with_schema(target_df)
    queries.write_from_dataframe(queries_df)

    return next()
