import dataiku 
import os


def get_input_full_name(recipe_id, input_id):
    """Returns a folder whether it is managed or shared
    
    Args:
        recipe_id (str): Id of the recipe whose parameter is a folder
        input_id (str): The id of the parameter. Can be recipe, models...

    Returns:
        dataiku.Folder: The associated folder handler
    """
    client = dataiku.api_client()
    project = client.get_project(dataiku.default_project_key())
    recipe = project.get_recipe(recipe_id)
    inputs = recipe.get_definition_and_payload().get_recipe_inputs()
    input_full_name = inputs[input_id]['items'][0]['ref']
    return input_full_name
