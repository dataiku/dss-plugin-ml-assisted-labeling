import logging
from abc import abstractmethod

from dataiku.customwebapp import *


class BaseClassifier(object):
    logger = logging.getLogger(__name__)

    @property
    @abstractmethod
    def type(self):
        pass

    def __init__(self):
        super(BaseClassifier, self).__init__()
        self.config = self.read_config()

    def read_config(self):
        config = get_webapp_config()
        self.logger.info("Webapp config: %s" % repr(config))

        if "labels_ds" not in config:
            raise ValueError("Labels dataset not specified. Go to settings tab.")

        return config

    @abstractmethod
    def get_all_sample_ids(self):
        pass

    @abstractmethod
    def get_sample_by_id(self, sid):
        pass
