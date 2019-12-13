import numpy as np
import dataiku
import os
import matplotlib
from PIL import Image
import errno


class ImgLoader:

    def __init__(self, *folders):
        self.folders = folders

    def fit(self, X, y=None, **kwargs):
        return self
    
    def transform(self, X):
        folder_paths = [dataiku.Folderfolder).get_path() for folder in self.folders]
        imgs = []
        for x in X:
            if x == '':
                imgs.append(np.asarray([]))
                continue
            for folder_path in folder_paths:
                x_in_path = os.path.join(folder_path, x.lstrip('/'))
                if os.path.exists(x_in_path):
                    img = np.ravel(Image.open(os.path.join(folder_path, x.lstrip('/'))))
                    imgs.append(img)
                    continue
                raise FileNotFoundError(
                    errno.ENOENT, os.strerror(errno.ENOENT), x)
        return np.asarray(imgs)