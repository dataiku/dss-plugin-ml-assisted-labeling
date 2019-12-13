import numpy as np
import dataiku
import os
import matplotlib
from PIL import Image
import errno


class ImgLoader:

    def __init__(self, *folders, verbose=0):
        self.folders = folders
        self.verbose = verbose

    def fit(self, X, y=None, **kwargs):
        return self
    
    def transform(self, X):
        folder_paths = [dataiku.Folder(folder).get_path() for folder in self.folders]
        imgs = []
        for x in X:
            if x == '':
                imgs.append(np.asarray([]))
                continue
            for folder_path in folder_paths:
                x_in_path = os.path.join(folder_path, x.lstrip('/'))
                if self.verbose > 0:
                    print("Checking existence of {} {}".format(x_in_path, os.path.exists(x_in_path)))
                if os.path.exists(x_in_path):
                    img = np.ravel(Image.open(x_in_path))
                    imgs.append(img)
                    break
            else:
                raise FileNotFoundError(
                    errno.ENOENT, os.strerror(errno.ENOENT), x)
        return np.asarray(imgs)