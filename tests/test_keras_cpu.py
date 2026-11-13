import importlib.util
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'python-lib'))


@unittest.skipUnless(importlib.util.find_spec('tensorflow'), 'TensorFlow is not installed')
class TestKerasSampler(unittest.TestCase):
    def test_confidence_sampling_with_keras_classifier(self):
        os.environ.setdefault('TF_NUM_INTRAOP_THREADS', '1')
        os.environ.setdefault('TF_NUM_INTEROP_THREADS', '1')
        os.environ.setdefault('OMP_NUM_THREADS', '1')
        import numpy as np
        import tensorflow as tf
        from cardinal.uncertainty import confidence_sampling

        model = tf.keras.Sequential([
            tf.keras.layers.Input(shape=(2,)),
            tf.keras.layers.Dense(2, activation='softmax', kernel_initializer='zeros', bias_initializer='zeros'),
        ])
        indices, scores = confidence_sampling(model, np.array([[1., 2.], [3., 4.]]), 2)
        self.assertEqual(len(indices), 2)
        np.testing.assert_allclose(scores, [0.5, 0.5])


if __name__ == '__main__':
    unittest.main()
