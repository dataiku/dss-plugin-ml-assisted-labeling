import numpy as np


from itertools import combinations

def new_halting_score(data):
    
    values, bins = np.histogram(data)  
    scores = values / values.sum()
    
    distances = np.zeros(55)
 
    for i, (min_unif, max_unif) in enumerate(combinations(np.arange(11), r=2)):

        local_uniform = np.zeros(10)
        local_uniform[min_unif:max_unif] = 1
        local_uniform /= local_uniform.sum()

        dist = np.abs(local_uniform - scores)
        distances[i] = dist.sum()
        
    ix_min = np.argmin(distances)
    min_dist = distances[ix_min]
      
    return min_dist


def quantile_constant(data, B=11, halting=True):

    quantiles = np.arange(0,1+1./B,1./B)
    quants = np.quantile(data,quantiles) 
    tol = 0.1
    
    #merging quantiles closer than tol - to merge locally uniform parts
    diffs = quants[1:] - quants[:-1]
    for i, diff in enumerate(diffs):
        if diff < tol:
            quants[i+1] = quants[i] 
    
    #assigning to each bins its mean uncertainty values
    bins = np.zeros(data.shape[0])
    binids = np.digitize(data,quants[:-1])-1
    for i in np.unique(binids):    
        bins[binids==i]= data[binids==i].mean()
        
    #to detect distribution too uniform
    if halting:
        index = np.linspace(0, 1, num=binids.shape[0])
        uniq_binids = np.unique(binids)
        for i in uniq_binids[::-1]:
            score = new_halting_score(bins[binids <= i])
            print("score:", np.sqrt(bins[binids == i].mean() / bins.max() * index[binids == i].mean()))
            if score < 0.2:
                bins[binids <= i] = 0
                break
    
    return bins, binids


def get_halting_values(scores):
    sorted_scores = np.sort(scores)
    _, binids = quantile_constant(sorted_scores)
    low_thr = sorted_scores[(binids <= 3)].max()
    high_thr = sorted_scores[(binids >= 8)].min()
    
    # Normalize scores from 0 to 1 for display
    vmin = scores.min()
    vmax = scores.max()
    
    scores = (vmax - scores) / vmin
    low_thr = (vmax - low_thr) / vmin
    high_thr = (vmax - high_thr) / vmin
    
    return scores, high_thr, low_thr  # Because of normalization we inverse low and high
