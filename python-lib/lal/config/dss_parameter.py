from .custom_check import CustomCheck, CustomCheckError
from typing import Any, List

import logging
logger = logging.getLogger(__name__)


class DSSParameterError(Exception):
    """Exception raised when at least one CustomCheck fails.
    """
    pass


class DSSParameter:
    """Object related to one parameter. It is mainly used for checks to run in backend for custom forms.

    Attributes:
        name(str): Name of the parameter
        value(Any): Value of the parameter
        checks(list[dict], optional): Checks to run on provided value
        required(bool, optional): Whether the value can be None
    """
    def __init__(self, name: str, value: Any, checks: List[dict] = None, required: bool = False):
        """Initialization method for the DSSParameter class

        Args:
            name(str): Name of the parameter
            value(Any): Value of the parameter
            checks(list[dict], optional): Checks to run on provided value
            required(bool, optional): Whether the value can be None
        """
        if checks is None:
            checks = []
        self.name = name
        self.value = value
        self.checks = [CustomCheck(**check) for check in checks]
        if required:
            self.checks.append(CustomCheck(type='exists'))
        self.run_checks()

    def run_checks(self):
        """Runs all checks provided for this parameter
        """
        errors = []
        for check in self.checks:
            try:
                check.run(self.value)
            except CustomCheckError as err:
                errors.append(err)
        if errors:
            self.handle_failure(errors)
        self.handle_success()

    def handle_failure(self, errors: List[CustomCheckError]):
        """Is called when at least one test fails. It will raise an Exception with understandable text

        Args:
            errors(list[CustomCheckError]: Errors met when running checks

        Raises:
            DSSParameterError: Raises if at least on check fails
        """
        raise DSSParameterError(self.format_failure_message(errors))

    def format_failure_message(self, errors: List[CustomCheckError]) -> str:
        """Format failure text

        Args:
            errors(list[CustomCheckError]: Errors met when running checks

        Returns:
            str: Formatted error message
        """
        return """
        Error for parameter \"{name}\" :
        {errors}
        Please check your settings and fix errors.
        """.format(
            name=self.name,
            errors='\n'.join(["\t- {}".format(e) for e in errors])
        )

    def handle_success(self):
        """Called if all checks are successful. Prints a success message
        """
        self.print_success_message()

    def print_success_message(self):
        """Formats the succee message
        """
        logger.info('All checks have been successfully done for {}.'.format(self.name))

    def __repr__(self):
        return "DSSParameter(name={}, value={})".format(self.name, self.value)

    def __str__(self):
        return "DSSParameter(name={}, value={})".format(self.name, self.value)
