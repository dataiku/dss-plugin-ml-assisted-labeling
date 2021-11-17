import logging
import dataiku
from dataiku.customrecipe import get_recipe_config, get_input_names_for_role, get_output_names_for_role
from ml_assisted_labeling_to_computer_vision.object_detection import format_labeling_plugin_annotations

logger = logging.getLogger(__name__)
dataset_df = dataiku.Dataset(get_input_names_for_role("input_dataset")[0]).get_dataframe()

target_column = get_recipe_config()["target_column"]
if target_column not in dataset_df.columns:
    raise Exception("Column {} not in dataset with columns {}".format(target_column, dataset_df.columns.tolist()))
logger.info("Annotations target column chosen: {}".format(target_column))

dataset_df[target_column] = format_labeling_plugin_annotations(dataset_df[target_column])

output_dataset = dataiku.Dataset(get_output_names_for_role("output_dataset")[0])
output_dataset.write_with_schema(dataset_df)
