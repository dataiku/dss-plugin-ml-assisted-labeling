import logging
from pickle import PickleError

import dataiku
import pandas as pd


def increment_queries_session(queries_ds_name):
    session_var_name = f'ML-ASSISTED-LABELING__{queries_ds_name}__session'
    variables = dataiku.Project().get_variables()
    session_id = variables['standard'].get(session_var_name, 0) + 1
    variables['standard'][session_var_name] = session_id
    dataiku.Project().set_variables(variables)
    return session_id


def get_current_session_id(queries_ds_name=None):
    if queries_ds_name is None:
        return 0
    return dataiku.Project().get_variables()['standard'].get(f'ML-ASSISTED-LABELING__{queries_ds_name}__session', 0)


def prettify_error(s):
    """Adds a blank and replaces regular spaces by non-breaking in the first 90 characters
    
    This function adds a big blank space and forces the first words to be a big block of
    unbreakable words. This enforces a newline in the DSS display and makes the error prettier.
    """
    return '\xa0' * 130 + ' \n' + s[:90].replace(' ', '\xa0') + s[90:]


def get_local_categories():
    return dataiku.Project().get_variables()['local'].get('ML-ASSISTED-LABELING__categories', [])


def load_classifier(dss_model, version_id=None):

    logging.info("Trying to load model from {0}".format(dss_model))
    try:
        clf = dss_model.get_predictor(version_id=version_id)._clf
    except Exception as e:
        raise PickleError(
            prettify_error('Failed to load the saved model. The visual Machine Learning '
                           'code environment needs to be compatible with the code environment of this plugin.' ) +
            prettify_error('Original error is {}'.format(e)))

    logging.info("Checking that model {0} is a classifier".format(dss_model))
    if len(dss_model.get_predictor(version_id=version_id).classes) == 0:
        raise TypeError(
            prettify_error('Saved model {} seems to be a regressor and not a classifier.'.format(saved_model_id) +
                           'Active learning in regression context is not supported yet.'))
    return clf


def load_data(input_dataset):
    
    # DSS entities loading
    logging.info("Reading samples from {0}".format(input_dataset))
    input_is_folder = False
    try:
        input_df = pd.DataFrame(dataiku.Dataset(input_dataset).get_dataframe())
        logging.info("{0} input is a dataset".format(input_dataset))
    except Exception as e:
        logging.info("{0} input is a folder".format(input_dataset))
        input_samples = dataiku.Folder(input_dataset)
        input_df = pd.DataFrame(input_samples.list_paths_in_partition(), columns=["path"])
        input_is_folder = True
        
    return input_df, input_is_folder


def preprocess_data(model, input_df, input_is_folder, version_id=None):
        
    try:
        input_X = model.get_predictor(version_id=version_id).get_preprocessing().preprocess(input_df)[0]
    except Exception as e:
        if input_is_folder and ("Failed to preprocess the following file" in str(e) or ('Managed folder name not found' in str(e))):
            raise LookupError(
                prettify_error('The model feature preprocessing could not be applied to the folder {}'.format(input_dataset) +
                               'This happens when the folder specified as image source in the visual '
                               'Machine Learning is different from the input folder of this recipe.') +
                prettify_error('Original error is {}'.format(e)))
        raise
     
    return input_X


def add_perf_metrics(metadata_name, model_version, n_samples, contradictions, auc):
    metrics_name = f'ML-ASSISTED-LABELING__{metadata_name}__metrics'

    variables = dataiku.Project().get_variables()
    standards = variables['standard']

    metrics = standards.get(metrics_name, [])
    metrics.append({"n_samples": n_samples,
                    "contradictions": contradictions,
                    "auc": auc,
                    "versionId": model_version})
    standards[metrics_name] = metrics

    variables['standard'] = standards
    dataiku.Project().set_variables(variables)


def get_perf_metrics(metadata_name):
    metrics_name = f'ML-ASSISTED-LABELING__{metadata_name}__metrics'

    variables = dataiku.Project().get_variables()
    standards = variables['standard']
    return standards.get(metrics_name, [])

