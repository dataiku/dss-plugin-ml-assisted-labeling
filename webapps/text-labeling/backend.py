import dataiku
from dataiku.customwebapp import get_webapp_config

from lal.api import define_endpoints
from lal.app_configuration import prepare_datasets
from lal.classifiers.text_classifier import TextClassifier
from lal.handlers.dataiku_lal_handler import DataikuLALHandler
from lal.config.dku_config import DkuConfig
from lal.utils import get_local_var


def create_dku_config(config):
    dku_config = DkuConfig()

    dku_config.add_param(
        name='unlabeled',
        value=config.get('unlabeled'),
        required=True
    )
    dku_config.add_param(
        name='text_column',
        value=config.get('text_column') or get_local_var('text_column'),
        required=True
    )
    categories = config.get('categories')
    categories_key = [c.get('from') for c in categories]
    dku_config.add_param(
        name='categories',
        value=categories,
        checks=[
            {
                'type': 'custom',
                'cond': all(categories_key),
                'err_msg': "All the categories must have a key. Aborting."
            },
            {
                'type': 'custom',
                'cond': len(categories_key) == len(set(categories_key)),
                'err_msg': "Categories key must be unique. Aborting."
            }],
        required=True
    )
    dku_config.add_param(
        name='labels_ds',
        value=config.get('labels_ds'),
        required=True
    )
    dku_config.add_param(
        name='metadata_ds',
        value=config.get('metadata_ds'),
        required=True
    )
    dku_config.add_param(
        name='metadata_ds',
        value=config.get('metadata_ds'),
        required=True
    )
    dku_config.add_param(
        name='label_col_name',
        value=config.get('label_col_name'),
        required=True
    )
    dku_config.add_param(
        name='use_prelabeling',
        value=config.get('use_prelabeling') or get_local_var('use_prelabeling'),
        required=True
    )
    dku_config.add_param(
        name='text_direction',
        value=config.get('text_direction') or get_local_var('text_direction'),
        checks=[{
            'type': 'in',
            'op': ['rtl', 'ltr']
        }],
        required=True
    )
    dku_config.add_param(
        name='tokenization_engine',
        value=config.get('tokenization_engine') or get_local_var('tokenization_engine'),
        checks=[{
            'type': 'in',
            'op': ['white_space', 'char']
        }],
        required=True
    )
    return dku_config


config = get_webapp_config()
dku_config = create_dku_config(config)
prepare_datasets(dku_config)
initial_df = dataiku.Dataset(config["unlabeled"]).get_dataframe()
queries_df = None


define_endpoints(app, DataikuLALHandler(TextClassifier(initial_df, queries_df, dku_config), dku_config))