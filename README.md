# ML Assisted Labeling Plugin  

This plugin lets you label your text, tabular, image or audio data efficiently by leveraging webapps and active learning recipes.

Not all samples bring the same amount of information when it comes to training a model. Labeling a very similar to an already labeled sample might not bring any improvement to the model performance. Active learning aims at estimating how much additional information labeling a sample can bring to a model and select the next sample to label accordingly.

Read the complete documentation on our [website](https://www.dataiku.com/product/plugins/ml-assisted-labeling/).

### Query sampling with DeepHub object detection

The object-detection app starts in manual-labeling mode. To enable its **Retrain model and refresh queries** action, first set up this Flow in the same project:

1. Use **Reformat image annotations** on the app's labels dataset, and train and deploy a native DeepHub object detection model using its output and the app's image folder.
2. Use **List folder contents** on that folder to create an image paths dataset. Use Prepare or Sample/Filter if needed to exclude non-image files and provide the path column expected by the model.
3. Score the image paths with the deployed model, keeping the path column. Connect the scored dataset, original image paths dataset and same image folder to **DeepHub object detection query sampler**. Set its output as **Queries** in the labeling webapp settings.

Pause labeling for all users before running the refresh action, and resume only after it succeeds and restarts the webapp. It rebuilds the annotations, trains the model, rebuilds the image paths, scores them, refreshes queries and restarts the webapp. A failure stops the remaining steps; in particular, training must activate a new model version. The check for labels changing during the refresh cannot prevent concurrent writes, so pausing labeling is required. If a new category is missing from the model, update and redeploy the model before refreshing. DeepHub excludes images with no object annotations from training.

The sampler uses `1 - confidence` for the highest-confidence detection per image; an empty detection list receives 1.0 and is prioritized for labeling. DSS and the underlying model can filter detections by confidence, so their thresholds affect the resulting order. The original dataset must list each image once, and every input image must have a prediction. Folder images not listed in that dataset are excluded from the queue. This recipe supports confidence sampling; margin and entropy require class scores that DeepHub's scoring output does not provide.

The legacy RetinaNet sampler and its object-detection-plugin training actions are no longer available. Existing RetinaNet weights cannot be used with the DeepHub sampler; train a native DeepHub model before scoring. The object-detection app template starts in manual-labeling mode: configure the scoring and query recipes and connect their output to the webapp to enable active learning.

## Running tests

Install [uv](https://docs.astral.sh/uv/) and run `make tests` with a supported Python version (3.9–3.13). Use `make tests PYTHON=python3.11` to select a different interpreter. The test environment includes the plugin's runtime requirements and development-only test tools. Unit test results are written to `tests/allure_report`.

Runtime dependencies are declared in `pyproject.toml` and resolved for all supported Python versions in `uv.lock`. After changing dependencies, run `make requirements` and commit the updated lock file and `code-env/python/spec/requirements.txt`; DSS installs from the generated requirements file. Run `make check-requirements` to check that the generated file is current. Development-only tools are excluded from the DSS requirements.

## License

The ML Assisted labeling plugin is:

   Copyright (c) 2019 Dataiku SAS

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

## Contributing

When you contribute code, you affirm that the contribution is your original work
and that you license the work to the project under the project's open source license.

Whether or not you state this explicitly, by submitting any copyrighted material via
pull request, email, or other means you agree to license the material under the
project's open source license and warrant that you have the legal authority to do so.
