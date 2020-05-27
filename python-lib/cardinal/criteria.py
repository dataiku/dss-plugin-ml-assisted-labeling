from itertools import combinations

import dataiku
import numpy as np

lal = dataiku.import_from_plugin('ml-assisted-labeling', 'lal')
from lal import utils


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
                bins[binids <= i] = data.min()
                break
    
    return bins, binids


def get_halting_values(scores):
    sorted_scores = np.sort(scores)
    _, binids = quantile_constant(sorted_scores)
    low_values = sorted_scores[(binids <= 3)]
    low_thr = low_values.max() if low_values.size else sorted_scores.min()
    high_values = sorted_scores[(binids >= 8)]
    high_thr = sorted_scores[:-20]
    if high_values.size:
        high_thr = min(high_values.min(), *high_thr)
    
    # Normalize scores from 0 to 1 for display
    vmin = scores.min()
    vmax = scores.max()
    
    scores = 1 - ((scores - vmin) / vmax)
    low_thr = 1 - ((low_thr - vmin) / vmax)
    high_thr = 1 - ((high_thr - vmin) / vmax)
    
    return scores, high_thr, low_thr  # Because of normalization we inverse low and high


def get_stopping_warning(metadata_name, contradiction_tol=.01, auc_tol=.01, lookback=3):
    metric = utils.get_perf_metrics(metadata_name)
    hist_contradictions = [x['contradictions'] for x in metric]
    hist_auc = [x['auc'] for x in metric]
    warn = []
    if len(metric) >= lookback:
        trigger = True
        for con1, con2 in zip(hist_contradictions[-(lookback - 1):], hist_contradictions[-lookback:-1]):
            trigger = np.abs(con1 - con2) < contradiction_tol
            if not trigger:
                break
        if trigger:
            warn.append('Contradictions have stalled for the past {} iterations.'.format(lookback))

    if len(metric) >= lookback:
        trigger = True
        for auc1, auc2 in zip(hist_auc[-(lookback - 1):], hist_auc[-lookback:-1]):
            trigger = np.abs(auc1 - auc2) < auc_tol
            if not trigger:
                break
        if trigger:
            warn.append('Classifier AUC has stalled for the past {} iterations.'.format(lookback))

    return warn