from lal.backend import define_endpoints
from lal.tabular_classifier import TabularClassifier

define_endpoints(app, TabularClassifier())
