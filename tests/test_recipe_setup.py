import importlib.util
from importlib.metadata import PackageNotFoundError
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


class TestRecipeSetup(unittest.TestCase):
    def test_classification_gpu_options_do_not_require_object_detection_plugin(self):
        dataiku = types.ModuleType('dataiku')
        dataiku.use_plugin_libs = MagicMock(side_effect=AssertionError('legacy plugin must not be loaded'))
        model = MagicMock()
        model.get_definition.return_value = {'contentType': 'prediction/keras'}
        dataiku.Model = MagicMock(return_value=model)
        path = Path(__file__).resolve().parents[1] / 'resource/recipes-helper.py'
        spec = importlib.util.spec_from_file_location('recipe_setup', path)
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {'dataiku': dataiku}), patch('importlib.metadata.version') as version:
            spec.loader.exec_module(module)
            inputs = [{'type': 'SAVED_MODEL', 'role': 'saved_model', 'fullName': 'my-model'}]
            for installed in ('tensorflow', 'tensorflow-gpu'):
                def check_package(name):
                    if name != installed:
                        raise PackageNotFoundError(name)
                    return '2.0'
                version.side_effect = check_package
                self.assertEqual(module.do({'method': 'get-gpu-info'}, {}, {}, inputs), {'can_use_gpu': True})
            model.get_definition.return_value = {'contentType': 'prediction/sklearn'}
            self.assertEqual(module.do({'method': 'get-gpu-info'}, {}, {}, inputs), {'can_use_gpu': False})
            version.side_effect = PackageNotFoundError
            self.assertEqual(module.do({'method': 'get-gpu-info'}, {}, {}, inputs), {'can_use_gpu': False})
        dataiku.use_plugin_libs.assert_not_called()


if __name__ == '__main__':
    unittest.main()
