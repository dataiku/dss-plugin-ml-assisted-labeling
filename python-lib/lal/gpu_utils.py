import os

import tensorflow as tf
from keras.backend.tensorflow_backend import set_session


def load_gpu_options(should_use_gpu, list_gpu, gpu_allocation):
    """Set up gpu configuration.
    
    Args:
        should_use_gpu: Boolean for gpu activation.
        list_gpu:       String of gpu uid separed by a comma.
        gpu_allocation: Gpu allocation percent.
        
    Returns:
        The gpu configurations.
    """
    gpu_options = {}
    if should_use_gpu:
        gpu_options['n_gpu'] = len(list_gpu.split(','))
        
        config = tf.ConfigProto()
        os.environ["CUDA_VISIBLE_DEVICES"] = list_gpu.strip()
        config.gpu_options.visible_device_list = list_gpu.strip()
        config.gpu_options.per_process_gpu_memory_fraction = gpu_allocation
        set_session(tf.Session(config=config))
    else:
        deactivate_gpu()
        gpu_options['n_gpu'] = 0

    return gpu_options


def deactivate_gpu():
    """Disable gpu."""
    os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

    
def can_use_gpu():
    """Check that system supports gpu."""
    # Check that 'tensorflow-gpu' is installed on the current code-env
    import pip
    installed_packages = pip.get_installed_distributions()
    return "tensorflow-gpu" in [p.project_name for p in installed_packages]


def set_gpus(gpus):
    """Short method to set gpu configuration."""
    config = tf.ConfigProto()
    config.gpu_options.visible_device_list = gpus.strip()
    set_session(tf.Session(config=config))