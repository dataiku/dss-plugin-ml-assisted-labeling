from lal.backend import define_endpoints
from lal.image_classifier import ImageClassifier

define_endpoints(app, ImageClassifier())
