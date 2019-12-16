from scipy.stats import entropy
from sklearn.base import BaseEstimator
import numpy as np


def _get_probability_classes(classifier, X):
    if classifier == 'precomputed':
        return X
    elif classifier.__class__.__module__.split('.')[0] == 'keras':  # Keras models have no predict_proba
        classwise_uncertainty = classifier.predict(X)
    else:  # sklearn compatible model
        classwise_uncertainty = classifier.predict_proba(X)
    return classwise_uncertainty


def confidence_sampling(classifier, X, n_instances=1):
    """Lowest confidence sampling query strategy. Selects the least sure instances for labelling.

    Args:
        classifier: The classifier for which the labels are to be queried.
        X: The pool of samples to query from.
        n_instances: Number of samples to be queried.

    Returns:
        The indices of the instances from X chosen to be labelled;
        the instances from X chosen to be labelled.
    """
    classwise_uncertainty = _get_probability_classes(classifier, X)
        
    # for each point, select the maximum uncertainty
    uncertainty = 1 - np.max(classwise_uncertainty, axis=1)
    index = np.flip(np.argsort(uncertainty))[:n_instances]
    
    return index, uncertainty[index]

def margin_sampling(classifier, X, n_instances=1):
    """Margin sampling query strategy, selects the samples with lowest difference between top 2 probabilities.

    This strategy takes the probabilities of top two classes and uses their
    difference as a score for selection.

    Args:
        classifier: The classifier for which the labels are to be queried.
        X: The pool of samples to query from.
        n_instances: Number of samples to be queried.

    Returns:
        The indices of the instances from X chosen to be labelled;
        the instances from X chosen to be labelled.
    """
    classwise_uncertainty = _get_probability_classes(classifier, X)

    part = np.partition(classwise_uncertainty, -2, axis=1)
    margin = 1 - (part[:, -1] - part[:, -2])
    index = np.flip(np.argsort(margin))[:n_instances]
    
    return index, margin[index]

def entropy_sampling(classifier, X, n_instances=1):
    """Entropy sampling query strategy, uses entropy of all probabilities as score.

    This strategy selects the samples with the highest entropy in their prediction
    probabilities.
    
    Args:
        classifier: The classifier for which the labels are to be queried.
        X: The pool of samples to query from.
        n_instances: Number of samples to be queried.

    Returns:
        The indices of the instances from X chosen to be labelled;
        the instances from X chosen to be labelled.
    """
    classwise_uncertainty = _get_probability_classes(classifier, X)
    
    entropies = np.transpose(entropy(np.transpose(classwise_uncertainty)))
    index = np.flip(np.argsort(entropies))[:n_instances]
    
    return index, entropies[index]