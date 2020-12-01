from .dss_parameter import DSSParameter



class DkuConfig(object):
    def __init__(self, config=None):
        if not config:
            config = {}
        self._load_param(config)

    def _load_param(self, config):
        self.config = config

    def add_param(self, name, **dss_param_kwargs):
        setattr(self, name, DSSParameter(name=name, **dss_param_kwargs))

    def get(self, key, default=None):
        print(key)
        return getattr(self, str(key), default)

    def __getattribute__(self, item):
        attr = object.__getattribute__(self, item)
        return attr.value if isinstance(attr, DSSParameter) else attr

    def __getitem__(self, item):
        it = self.get(item)
        if not it:
            raise KeyError(item)
        return self.get(item)

    def __contains__(self, item):
        return not not self.get(item)
