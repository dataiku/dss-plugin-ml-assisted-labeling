import importlib.util
import os
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


class TestGPUOptions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).resolve().parents[1] / 'python-lib/lal/gpu_utils.py'
        spec = importlib.util.spec_from_file_location('gpu_utils', path)
        cls.gpu = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.gpu)

    def test_cpu_does_not_require_tensorflow(self):
        with patch.dict(os.environ, {}, clear=True), patch.dict(sys.modules, {'tensorflow': None}):
            self.assertEqual(self.gpu.load_gpu_options(False, '', 0.5), {'n_gpu': 0})
            self.assertEqual(os.environ['CUDA_VISIBLE_DEVICES'], '-1')

    def test_gpu_preserves_session_configuration(self):
        tf = types.ModuleType('tensorflow')
        dss_gpu = types.ModuleType('dataiku.doctor.deep_learning.gpu')
        dss_gpu.load_gpu_options = MagicMock()
        backend = types.ModuleType('tensorflow.keras.backend')
        backend.clear_session = MagicMock()
        internal_backend = types.ModuleType('tensorflow.python.keras.backend')
        internal_backend.clear_session = MagicMock()
        internal_keras = types.ModuleType('tensorflow.python.keras')
        internal_keras.backend = internal_backend
        modules = {'tensorflow': tf, 'tensorflow.keras': types.ModuleType('tensorflow.keras'),
                   'tensorflow.keras.backend': backend, 'dataiku': types.ModuleType('dataiku'),
                   'dataiku.doctor': types.ModuleType('dataiku.doctor'),
                   'dataiku.doctor.deep_learning': types.ModuleType('dataiku.doctor.deep_learning'),
                   'dataiku.doctor.deep_learning.gpu': dss_gpu,
                   'tensorflow.python': types.ModuleType('tensorflow.python'),
                   'tensorflow.python.keras': internal_keras,
                   'tensorflow.python.keras.backend': internal_backend}
        with patch.dict(os.environ, {}, clear=True), patch.dict(sys.modules, modules):
            self.assertEqual(self.gpu.load_gpu_options(True, '1', 0.5), {'n_gpu': 1})
            self.assertEqual(os.environ['CUDA_VISIBLE_DEVICES'], '1')
            dss_gpu.load_gpu_options.assert_called_once_with(['1'], per_process_gpu_memory_fraction=0.5)
            self.gpu.reset_session()
            backend.clear_session.assert_called_once()
            internal_backend.clear_session.assert_called_once()


if __name__ == '__main__':
    unittest.main()
