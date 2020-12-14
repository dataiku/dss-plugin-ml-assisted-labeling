import logging
logger = logging.getLogger(__name__)

DEFAULT_ERROR_MESSAGES = {
    'exists': 'The field "{name}" is required.',
    'in': '{value} should be in the following iterable: {op}.',
    'not_in': '{value} should not be in the following iterable: {op}.',
    'sup': '{name} should be superior to {op} (Currently {value}).',
    'sup_eq': '{name} should be superior or equal to {op} (Currently {value}).',
    'inf': '{name} should be inferior to {op} (Currently {value}).',
    'inf_eq': '{name} should be inferior or equal to {op} (Currently {value}).',
    'between': '{name} should be between {op[0]} and {op[1]} (Currently {value}).',
    'between_strict': '{name} should be strictly between {op[0]} and {op[1]} (Currently {value}).',
    'custom': "Unknown error append."
}


class DSSParameterError(Exception):
    pass


class CustomCheck:
    def __init__(self, type, op=None, cond=None, err_msg='', severity='ERROR'):
        self.type = type
        self.op = op
        self.cond = cond
        self.err_msg = err_msg or self.get_default_err_msg()
        self.severity = getattr(logging, severity, logging.ERROR)

    def run(self, parameter):
        result = getattr(self, '_{}'.format(self.type))(parameter.value)
        self.handle_return(result, parameter)

    def handle_return(self, result, parameter):
        try:
            assert result
        except AssertionError:
            formatted_err_msg = self.format_err_mesg(parameter)
            if self.severity == logging.ERROR:
                raise DSSParameterError(formatted_err_msg)
            else:
                logger.log(self.severity, formatted_err_msg)

    def get_default_err_msg(self):
        return DEFAULT_ERROR_MESSAGES[self.type]

    def format_err_mesg(self, parameter):
        formatted_err_msg = self.err_msg.format(name=parameter.name, value=parameter.value, op=self.op)
        return f'Error for parameter "{parameter.name}" - {formatted_err_msg}'

    def _exists(self, value):
        if "nguages, you can use \"Detected language" in self.err_msg:
            print("value : ", value)
        return not value is None

    def _in(self, value):
        return value in self.op

    def _not_in(self, value):
        return value not in self.op

    def _sup(self, value):
        return value > float(self.op)

    def _inf(self, value):
        return value < float(self.op)

    def _sup_eq(self, value):
        return value >= float(self.op)

    def _inf_eq(self, value):
        return value <= float(self.op)

    def _between(self, value):
        return float(self.op[0]) <= value <= float(self.op[1])

    def _between_strict(self, value):
        return float(self.op[0]) < value < float(self.op[1])

    def _is_type(self, value):
        return isinstance(value, self.op)

    def _custom(self, value):
        return self.cond


class DSSParameter:
    def __init__(self, name, value, checks=None, required=False):
        if checks is None:
            checks = []
        self.name = name
        self.value = value
        self.checks = [CustomCheck(**check) for check in checks]
        self.required = required
        self.run_checks()

    def run_checks(self):
        if self.required:
            self.checks.append(CustomCheck(type='exists'))
        for check in self.checks:
            check.run(self)

        self.print_success_message()

    def print_success_message(self):
        logger.info('All checks have been successfully done for {}.'.format(self.name))

