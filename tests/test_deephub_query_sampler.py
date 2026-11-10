import sys
import unittest
from pathlib import Path
from runpy import run_path
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'python-lib'))
from deephub_query_sampler import make_queries


class TestDeepHubQuerySampler(unittest.TestCase):
    def test_detections_and_empty_predictions(self):
        rows = [
            ('nested/a.jpg', '[{"confidence": 0.2}, {"confidence": 0.8}]'),
            ('/b.jpg', '[]'),
        ]
        self.assertEqual(make_queries(rows, ['/nested/a.jpg', 'b.jpg'],
                                      ['/nested/a.jpg', '/b.jpg', '/metadata.json']),
                         [('/nested/a.jpg', 1 - 0.8), ('/b.jpg', 1.0)])

    def test_invalid_predictions_are_rejected(self):
        for prediction in ('', 'null', '{}', '[{}]', '[{"confidence": true}]',
                           '[{"confidence": NaN}]', '[{"confidence": 1.1}]'):
            with self.subTest(prediction=prediction):
                with self.assertRaises(ValueError):
                    make_queries([('a', prediction)], ['a'], ['/a'])

    def test_missing_duplicate_and_unknown_paths_are_rejected(self):
        cases = [
            ([], ['a'], ['/a']),
            ([('a', '[]'), ('/a', '[]')], ['a'], ['/a']),
            ([('a', '[]')], ['a', '/a'], ['/a']),
            ([('b', '[]')], ['a'], ['/a', '/b']),
            ([('a', '[]')], ['a'], ['/b']),
            ([], [], []),
            ([(None, '[]')], ['a'], ['/a']),
        ]
        for rows, inputs, folder in cases:
            with self.subTest(rows=rows, inputs=inputs, folder=folder):
                with self.assertRaises(ValueError):
                    make_queries(rows, inputs, folder)

    def test_recipe_writes_before_advancing_session(self):
        output = SimpleNamespace(short_name='queries', write_with_schema=Mock())
        datasets = {
            'scored': SimpleNamespace(get_dataframe=lambda: {'path': ['a'], 'prediction': ['[]']}),
            'input': SimpleNamespace(get_dataframe=lambda: {'path': ['a']}),
            'queries': output,
        }
        dataiku = ModuleType('dataiku')
        dataiku.Dataset = datasets.__getitem__
        dataiku.Folder = lambda name: SimpleNamespace(list_paths_in_partition=lambda: ['/a'])
        customrecipe = ModuleType('dataiku.customrecipe')
        customrecipe.get_recipe_config = lambda: {'path_column': 'path', 'prediction_column': 'prediction',
                                                   'input_path_column': 'path'}
        customrecipe.get_input_names_for_role = lambda role: [{'predictions': 'scored', 'input_images': 'input',
                                                               'images': 'folder'}[role]]
        customrecipe.get_output_names_for_role = lambda role: ['queries']
        pandas = ModuleType('pandas')
        pandas.DataFrame = lambda values, columns: (values, columns)
        lal = ModuleType('lal')
        lal.utils = SimpleNamespace(increment_queries_session=Mock())
        output.write_with_schema.side_effect = lambda value: lal.utils.increment_queries_session.assert_not_called()
        path = Path(__file__).resolve().parents[1] / 'custom-recipes/deephub-object-detection-query-sampler/recipe.py'
        with patch.dict(sys.modules, {'dataiku': dataiku, 'dataiku.customrecipe': customrecipe,
                                      'pandas': pandas, 'lal': lal}):
            run_path(str(path))
        output.write_with_schema.assert_called_once_with(([('/a', 1.0)], ['path', 'uncertainty']))
        lal.utils.increment_queries_session.assert_called_once_with('queries')


if __name__ == '__main__':
    unittest.main()
