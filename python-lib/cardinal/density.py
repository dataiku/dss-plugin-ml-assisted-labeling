from sklearn.metrics.pairwise import pairwise_distances
import numpy as np
from typing import Callable, Union


def density_sampling(X: np.ndarray,
                     idx_labeled: np.ndarray = None,
                     n_instances: int = 1,
                     metric: Union[str, Callable] = 'euclidean') -> np.ndarray:
    """
    Random sampling query strategy. Selects instances randomly
    
    Args:
        X: The pool of samples to query from.
        idx_labelled: Samples to remove because they have been already labelled
        n_instances: Number of samples to be queried.
        metric: Optional, default is euvlidean. Metric matching the sklearn definition.

    Returns:
        The indices of the instances from X chosen to be labelled;
        the instances from X chosen to be labelled.
        
    Note:
        This class is handy for testing against naive method
    """
    
    similarity_mtx = 1 / (1 + pairwise_distances(X, X, metric=metric))
    similarity = similarity_mtx.mean(axis=1)
    index = np.flip(np.argsort(similarity))
    if idx_labelled is not None:
        # Note: probably note the most efficient way to do it
        index = np.extract(np.logical_not(np.isin(idx_labeled, index)), index)
    index = index[:n_instances]

    return index, similarity[index]