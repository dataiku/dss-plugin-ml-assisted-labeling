from .dss_parameter import DSSParameter
import dataiku


class DkuConfig(object):
    def __init__(self, config=None, use_local=False, local_prefix=''):
        self.use_local = use_local
        self.local_prefix = local_prefix
        self._load_param(config)

    def _load_param(self, config):
        self.config = config or {}

    def _get_local_var(self, var_name):
        return dataiku.Project().get_variables()['local'].get('{}__{}'.format(self.local_prefix, var_name), None)

    def add_param(self, name, **dss_param_kwargs):
        if self.use_local:
            dss_param_kwargs['value'] = dss_param_kwargs.get('value') or self._get_local_var(name)

        setattr(self, name, DSSParameter(name=name, **dss_param_kwargs))

    def get(self, key, default=None):
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
