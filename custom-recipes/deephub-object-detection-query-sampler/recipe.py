import pandas as pd
import dataiku
from dataiku.customrecipe import get_input_names_for_role, get_output_names_for_role, get_recipe_config

from deephub_query_sampler import make_queries
from lal import utils

config = get_recipe_config()
scored = dataiku.Dataset(get_input_names_for_role('predictions')[0]).get_dataframe()
input_images = dataiku.Dataset(get_input_names_for_role('input_images')[0]).get_dataframe()
folder = dataiku.Folder(get_input_names_for_role('images')[0])
rows = zip(scored[config['path_column']], scored[config['prediction_column']])
queries = make_queries(rows, input_images[config['input_path_column']], folder.list_paths_in_partition())
output = dataiku.Dataset(get_output_names_for_role('queries')[0])
output.write_with_schema(pd.DataFrame(queries, columns=['path', 'uncertainty']))
utils.increment_queries_session(output.short_name)
