from itertools import combinations

import numpy as np
import logging

try:
    import dataiku
    lal = dataiku.import_from_plugin('ml-assisted-labeling', 'lal')
except Exception as e:
    logging.warning("Couldn't import lal from ml-assisted-labeling plugin, will assume it's already in PYTHONPATH")
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

    quantiles = np.arange(0, 1 + 1. / B, 1. / B)
    quants = np.quantile(data, quantiles)
    tol = 0.1
    
    # Merging quantiles closer than tol - to merge locally uniform parts
    diffs = quants[1:] - quants[:-1]
    for i, diff in enumerate(diffs):
        if diff < tol:
            quants[i+1] = quants[i] 
    
    # Assigning to each bins its mean uncertainty values
    bins = np.zeros(data.shape[0])
    binids = np.digitize(data, quants[:-1])-1
    for i in np.unique(binids):    
        bins[binids == i] = data[binids == i].mean()
        
    # To detect distribution too uniform
    if halting:
        index = np.linspace(0, 1, num=binids.shape[0])
        uniq_binids = np.unique(binids)
        for i in uniq_binids[::-1]:
            score = new_halting_score(bins[binids <= i])
            if score < 0.2:
                bins[binids <= i] = data.min()
                break
    
    return bins, binids


def get_halting_values(scores):
    n = scores.shape[0]
    sorted_scores = np.sort(scores)
    _, binids = quantile_constant(sorted_scores)

    # Because the data is sorted, the binids too. We can retrieve the index easily
    low_indices = np.where(binids <= 1)[0]
    low_index = low_indices[-1] if low_indices.size else 0

    high_indices = np.where(binids >= 10)[0]
    high_index = high_indices[0] if high_indices.size else n - 10
    # Force at least 10 samples to be green
    high_index = max(min(n - 10, high_index), 0)

    # Normalize scores from 0 to 1 for display
    vmin = scores.min()
    vmax = scores.max()

    if vmax == vmin:
        return 1 - scores, vmin, vmax

    scores = 1 - ((scores - vmin) / (vmax - vmin))
    argsort = np.argsort(scores)

    # Force a linear space between samples
    scores *= argsort / n

    # Because indices are reverted, we revert the thesholds
    low_thr = scores[n - high_index - 1]
    high_thr = scores[n - low_index - 1]
    
    return scores, low_thr, high_thr


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
