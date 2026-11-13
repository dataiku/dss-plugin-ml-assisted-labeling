import os
import sys


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
        os.environ["CUDA_VISIBLE_DEVICES"] = list_gpu.strip()
        from dataiku.doctor.deep_learning.gpu import load_gpu_options as load_dss_gpu_options
        gpu_list = [gpu.strip() for gpu in list_gpu.split(',')]
        load_dss_gpu_options(gpu_list, per_process_gpu_memory_fraction=gpu_allocation)
        gpu_options['n_gpu'] = len(gpu_list)
    else:
        deactivate_gpu()
        gpu_options['n_gpu'] = 0

    return gpu_options


def reset_session():
    if 'tensorflow' in sys.modules:
        from tensorflow.python.keras import backend as legacy_backend
        from tensorflow.keras.backend import clear_session
        legacy_backend.clear_session()
        clear_session()


def deactivate_gpu():
    """Disable gpu."""
    os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
