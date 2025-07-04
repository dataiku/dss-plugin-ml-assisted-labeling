import os

from lal import utils
import tensorflow as tf

if utils.package_is_at_least(tf, "2.14"):
    import tensorflow.python.keras.backend as K
    set_session = K.set_session
    clear_session = K.clear_session
else:
    set_session = tensorflow.compat.v1.keras.backend.set_session
    clear_session = tensorflow.compat.v1.keras.backend.clear_session


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


def reset_session():
    clear_session()


def deactivate_gpu():
    """Disable gpu."""
    os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

    
def set_gpus(gpus):
    """Short method to set gpu configuration."""
    config = tf.ConfigProto()
    config.gpu_options.visible_device_list = gpus.strip()
    set_session(tf.Session(config=config))