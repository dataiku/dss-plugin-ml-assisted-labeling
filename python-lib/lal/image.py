import numpy as np
import dataiku
import os
import matplotlib
matplotlib.use('agg')
from matplotlib.pyplot import imread


class ImgLoader:

    def __init__(self, folder):
        self.folder = folder

    def fit(self, X, y=None, **kwargs):
        return self
    
    def transform(self, X):
        folder_path = dataiku.Folder(self.folder).get_path()
        imgs = []
        for x in X:
            img = np.ravel(imread(os.path.join(folder_path, x.lstrip('/'))))
            imgs.append(img)
        return np.asarray(imgs)