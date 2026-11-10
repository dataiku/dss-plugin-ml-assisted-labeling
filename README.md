# ML Assisted Labeling Plugin  

This plugin lets you label your text, tabular, image or audio data efficiently by leveraging webapps and active learning recipes.

Not all samples bring the same amount of information when it comes to training a model. Labeling a very similar to an already labeled sample might not bring any improvement to the model performance. Active learning aims at estimating how much additional information labeling a sample can bring to a model and select the next sample to label accordingly.

Read the complete documentation on our [website](https://www.dataiku.com/product/plugins/ml-assisted-labeling/).

### Query sampling with DeepHub object detection

Score an image dataset with a native DeepHub object detection model, keeping the image path column in the scoring output. Run the **DeepHub object detection query sampler** with the original image dataset, its image folder, and the scoring output. Select the path columns and the prediction column; configure the resulting queries dataset in the image object labeling webapp. After adding labels, retrain the model, rerun scoring and the sampler, and restart the webapp.

The sampler uses `1 - confidence` for the highest-confidence detection per image; an empty detection list receives 1.0 and is prioritized for labeling. DSS and the underlying model can filter detections by confidence, so their thresholds affect the resulting order. The original dataset must list each image once, and every input image must have a prediction. Folder images not listed in that dataset are excluded from the queue. This recipe supports confidence sampling; margin and entropy require class scores that DeepHub's scoring output does not provide.

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
