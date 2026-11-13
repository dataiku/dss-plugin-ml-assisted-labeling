import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd


class TestLabelPersistence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base = types.ModuleType('lal.classifiers.base_classifier')
        base.BaseClassifier = object
        utils = types.ModuleType('lal.utils')
        utils.get_local_categories = lambda: []
        modules = {'lal': types.ModuleType('lal'), 'lal.classifiers': types.ModuleType('lal.classifiers'),
                   'lal.classifiers.base_classifier': base, 'lal.utils': utils}
        path = Path(__file__).resolve().parents[1] / 'python-lib/lal/handlers/lal_handler.py'
        spec = importlib.util.spec_from_file_location('test_lal_handler', path)
        cls.module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, modules):
            spec.loader.exec_module(cls.module)

    def setUp(self):
        classifier = MagicMock()
        classifier.use_prelabeling = False
        classifier.get_raw_item_by_id.return_value = {'path': '/image.jpg'}
        classifier.serialize_label.side_effect = lambda label: str(label)
        classifier.get_session.return_value = 3
        meta = pd.DataFrame(columns=['label_id', 'label', 'date', 'data_id', 'status', 'comment', 'session', 'annotator'])
        labels = pd.DataFrame(columns=['label_id', 'path', 'label'])
        self.handler = self.module.LALHandler(classifier, 'label', meta, labels)
        self.handler.calculate_stats = MagicMock(return_value={})
        self.handler.save_item_label = MagicMock()
        self.handler.save_item_meta = MagicMock()

    def test_label_relabel_and_skip_persist_single_record(self):
        result = self.handler.label({'id': 'image', 'label': ['cat']}, 'user')
        self.assertEqual(result['label_id'], 1)
        self.handler.label({'id': 'image', 'label': ['dog']}, 'user')
        self.assertEqual(len(self.handler.labels_df), 1)
        self.assertEqual(self.handler.labels_df.iloc[0]['label'], "['dog']")
        self.assertEqual(self.handler.meta_df.iloc[0]['status'], 'LABELED')
        self.handler.skip({'dataId': 'image', 'labelId': 1}, 'user')
        self.assertTrue(self.handler.labels_df.empty)
        self.assertEqual(len(self.handler.meta_df), 1)
        self.assertEqual(self.handler.meta_df.iloc[0]['status'], 'SKIPPED')
        self.assertEqual(self.handler.meta_df.iloc[0]['data_id'], 'image')
        self.handler.save_item_meta.assert_called()
        self.handler.save_item_label.assert_called()


if __name__ == '__main__':
    unittest.main()
