# ML Assisted Labeling Plugin  

This plugin lets you label your text, tabular, image or audio data efficiently by leveraging webapps and active learning recipes.

Not all samples bring the same amount of information when it comes to training a model. Labeling a very similar to an already labeled sample might not bring any improvement to the model performance. Active learning aims at estimating how much additional information labeling a sample can bring to a model and select the next sample to label accordingly.

Read the complete documentation on our [website](https://www.dataiku.com/product/plugins/ml-assisted-labeling/).

### Query sampling with DeepHub object detection

The object-detection app starts in manual-labeling mode. Upload images to **Source images**, configure the categories, start the labeling webapp and label some images. To enable its **Retrain model and refresh queries** action, first set up this Flow in the same project:

1. Use **Reformat image annotations** on the app's labels dataset, and train and deploy a native DeepHub object detection model using its output and the app's image folder.
2. Use **List folder contents** on that folder to create an image paths dataset. Use Prepare or Sample/Filter if needed to exclude non-image files and provide the path column expected by the model.
3. Score the image paths with the deployed model, keeping the path column. Connect the scored dataset, original image paths dataset and same image folder to **DeepHub object detection query sampler**. Set its output as **Queries** in the labeling webapp settings.

Pause labeling for all users before running the refresh action, and resume only after it succeeds and restarts the webapp. It rebuilds the annotations, trains the model, rebuilds the image paths, scores them, refreshes queries and restarts the webapp. A failure stops the remaining steps; in particular, training must activate a new model version. The check for labels changing during the refresh cannot prevent concurrent writes, so pausing labeling is required. If a new category is missing from the model, update and redeploy the model before refreshing. DeepHub excludes images with no object annotations from training.

The sampler uses `1 - confidence` for the highest-confidence detection per image; an empty detection list receives 1.0 and is prioritized for labeling. DSS and the underlying model can filter detections by confidence, so their thresholds affect the resulting order. The original dataset must list each image once, and every input image must have a prediction. Folder images not listed in that dataset are excluded from the queue. This recipe supports confidence sampling; margin and entropy require class scores that DeepHub's scoring output does not provide.

The legacy RetinaNet sampler and its object-detection-plugin training actions are no longer available. Existing RetinaNet weights cannot be used with the DeepHub sampler; train a native DeepHub model before scoring. The object-detection app template starts in manual-labeling mode: configure the scoring and query recipes and connect their output to the webapp to enable active learning.

## Running tests

Install [uv](https://docs.astral.sh/uv/) and run `make tests` with a supported Python version (3.9–3.13). Use `make tests PYTHON=python3.11` to select a different interpreter. The test environment includes the plugin's runtime requirements and development-only test tools. Unit test results are written to `tests/allure_report`.

Runtime dependencies are declared in `pyproject.toml`. After changing dependencies, run `make requirements` and commit `code-env/python/spec/requirements.txt`; DSS installs from the generated requirements file. Run `make check-requirements` to check that the generated file is current. These targets use `uv export` and a local `uv.lock` to resolve and pin dependencies across the supported Python versions. Development-only tools are excluded from the DSS requirements. Tests use the same project dependencies and lockfile, with their development or integration dependency groups.

The plugin version and DSS metadata are declared in `pyproject.toml`. After changing them, run `make plugin-json` and commit both `pyproject.toml` and the generated `plugin.json`. Run `make check-plugin-json` to check for drift. `make plugin` packages the committed `HEAD` snapshot and checks that the committed metadata and manifest agree before building the archive.

To run the integration tests, set `DSS_URL` and `DSS_API_KEY` and run `make integration-tests`. The API key must be able to create and delete app instances, datasets, and recipes. The plugin and its code environment must be installed and usable on that DSS instance. `make tests` also runs the integration tests and requires these settings; use `make unit-tests` to run without DSS. The integration tests create temporary object-detection app instances and delete them after each test. They exercise annotation conversion and query sampling with synthetic predictions; they do not train a DeepHub model or test labeling through the webapp.

For a real retraining and query refresh, create a dedicated test-only app instance and set up the DeepHub Flow described above, including labeled images, an active model, the query sampler and the webapp's Queries setting. The DSS DeepHub object-detection code environment and any required model resources must be available. Set `DSS_ML_LABELING_FIXTURE_PROJECT` to its project key and run `make integration-refresh-test`. The API key also needs permission to duplicate and delete projects, train models, run scenarios and start webapps. The test duplicates the fixture, runs the shipped refresh scenario on the copy, checks the new model version, query values and webapp restart, and removes the copy. For safe duplication, use local managed datasets on `filesystem_managed` with paths of the form `${projectKey}/name`, and folders on `filesystem_folders` with paths of the form `${projectKey}/name` or `${projectKey}/${odbId}`; `name` must be a single component containing only letters, digits, underscores or hyphens. Shared objects and partitioned datasets are rejected. This test does not automate the initial creation of the DeepHub model or exercise the labeling UI.

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
