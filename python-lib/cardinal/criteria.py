import numpy as np


def halting_score(data, min_data=None, max_data=None):
    """Compute halting score from an array of uncertainty score 

    Parameters
    ----------
    data: array, shape (n_samples,)
        Active Learning scores on unlabeled data.
    
    min_data: float, optional (default=None)
        Minimum score for binning. If None, the minimum score of data will be used.

    max_data: float, optional (default=None)
        Maximum score for binning. If None, the maximum score of data will be used.
        
    Return
    ------
    score: float
        Halting score for the data.
        
    min_data: float
        Minimum score.   
        
    max_data: float
        Maximum score.
    
    width: float
        Width in data binning.
    """

    if not min_data:
        min_data = data.min()
    if not max_data:
        max_data = data.max()
    
    # Binning
    bins, width = np.linspace(min_data,max_data, num=11, retstep=True)
    binids = np.digitize(data, bins[:-1]) - 1
    bin_sums = np.bincount(np.sort(binids), minlength=10)

    # Norm integral
    density = bin_sums / float(bin_sums.sum())
    score = np.cumsum(density).sum() * width

    return score, min_data, max_data, width
    
    
def halting_test(data, min_data=None, max_data=None):
    """Compute halting test from an array of uncertainty score. By computing it for
    the given data as well as for uniform data on the same range and uniform on the 
    last bin.

    Parameters
    ----------
    data: array, shape (n_samples,)
        Active Learning scores on unlabeled data.
    
    min_data: float, optional (default=None)
        Minimum score for binning. If None, the minimum score of data will be used.

    max_data: float, optional (default=None)
        Maximum score for binning. If None, the maximum score of data will be used.
        
    Return
    ------
    test: float
        Halting score for the data.
        
    test_uniform: float
        Halting score for uniform data between min_data and max_data
        
    """
    
    score, min_test, max_test, width = halting_score(data, min_data=None, max_data=None)
    
    uniform_score, _, _, _ = halting_score(
        np.random.uniform(low=min_test, high=max_test, size = 10000),
        min_data=min_test, max_data=max_test)
    
    min_right_dirac = max_test - width
    right_dirac_score, _, _, _ = halting_score(
        np.random.uniform(low=min_right_dirac, high=max_test, size = 10000),
        min_data=min_test, max_data=max_test)

    return {'test' : score,
            'test_uniform': uniform_score,
            'test_right_dirac': right_dirac_score
           }
    

def weighted_sample_score(sample_value, halting_score, min_value, max_value):
    """Weighted decay to score sample from unlabeled batch.

    Parameters
    ----------
    sample_value: float
        Uncertainty value of the sample to score.  
        
    halting_score: float
        Halting score previously computed.

    min_value: float
        Minimum uncertainty score.

    max_value: float
        Maximum uncertainty score.
        
    Return
    ------
    score: float
        Sample score
    """
    if max_value == min_value:
        return halting_score
    else:
        return halting_score * (1 - (max_value - sample_value) / float(max_value - min_value))


def get_halting_values(scores):
    test = halting_test(scores)
    halting_score = test['test']
    min_score = scores.min()
    max_score = scores.max()
    values = np.asarray([weighted_sample_score(x, hs, min_score, max_score) for x in scores])
    low_thr =  (2 * min_score + max_score) / 3.
    high_thr = (min_score + 2 * max_score) / 3.
    return values, low_thr, high_thr