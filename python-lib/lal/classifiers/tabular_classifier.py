import hashlib
import logging

from lal.classifiers.base_classifier import BaseClassifier


class TabularClassifier(BaseClassifier):
    logger = logging.getLogger(__name__)

    def __init__(self, initial_df, queries_df, config=None):
        self.__initial_df = initial_df
        super(TabularClassifier, self).__init__(queries_df, config)

    def get_initial_df(self):
        return self.__initial_df

    def raw_row_to_id(self, raw):
        return str(hash(tuple(raw)))

    @property
    def type(self):
        return 'tabular'
