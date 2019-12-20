import dataiku 
import os


def get_folder_from_recipe(recipe_id, folder_id):
    """Returns a folder whether it is managed or shared
    
    Args:
        recipe_id (str): Id of the recipe whose parameter is a folder
        folder_id (str): The id of the folder

    Returns:
        dataiku.Folder: The associated folder handler
    """
    client = dataiku.api_client()
    project = client.get_project(dataiku.default_project_key())
    recipe = project.get_recipe(recipe_id)
    inputs = recipe.get_definition_and_payload().get_recipe_inputs()
    folder_full_name = inputs['unlabeled_samples']['items'][0]['ref']
    return dataiku.Folder(folder_full_name)
