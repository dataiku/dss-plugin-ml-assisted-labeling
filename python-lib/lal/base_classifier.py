from abc import abstractmethod


class BaseClassifier(object):
    @abstractmethod
    def get_all_sample_ids(self):
        pass

    @abstractmethod
    def get_labeled_sample_ids(self):
        pass

    @abstractmethod
    def get_sample_by_id(self, sid):
        pass
