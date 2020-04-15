import numpy as np
import statsmodels.api as sm


def halting_criterion(values):
    
    index = np.argsort(values)
    
    data = np.cumsum(values[index])
    
    X = np.arange(data.shape[0])
    ols_X = sm.add_constant(X)
    model = sm.OLS(data,ols_X)
    results = model.fit()
    thr = lambda x: results.params[0] + results.params[1] * x
    thr = thr(X)
    pos = np.where((data - thr) < 0)[0]
    min_thr = pos[0]
    max_thr = pos[-1] + 1
    final = np.ones(data.shape[0])
    final[index[min_thr:max_thr]] = 2
    final[index[max_thr:]] = 3
    
    return final