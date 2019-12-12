import numpy as np
import dataiku
import os
import matplotlib
from PIL import Image


class ImgLoader:

    def __init__(self, folder):
        self.folder = folder

    def fit(self, X, y=None, **kwargs):
        return self
    
    def transform(self, X):
        folder_path = dataiku.Folder(self.folder).get_path()
        imgs = []
        for x in X:
            if x == '':
                imgs.append(np.asarray([]))
                continue
            img = np.ravel(Image.open(os.path.join(folder_path, x.lstrip('/'))))
            imgs.append(img)
        return np.asarray(imgs)