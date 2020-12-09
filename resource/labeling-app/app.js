import {CategorySelector} from "./components/category-selector.js";
import {SoundSample} from "./components/sound-sample.js";
import {TabularSample} from "./components/tabular-sample.js";
import {ControlButtons} from "./components/control-buttons.js";
import {APIErrors, DKUApi} from "./dku-api.js";
import {ErrorsComponent} from "./components/errors.js";
import {ImageSample} from "./components/image-sample.js";
import {ImageCanvas} from "./components/image-object-sample/ImageCanvas.js";
import {TextArea} from "./components/text-sample/textArea.js";
import {loadConfig, savePerIterationConfig} from './components/utils/utils.js'
import {HaltingCriterionMetric} from "./components/halting-criterion-metric.js";
import {config} from './components/utils/utils.js'

Vue.use(VTooltip);

export default new Vue({
    el: '#app',
    components: {
        'category-selector': CategorySelector,
        'image-sample': ImageSample,
        'sound-sample': SoundSample,
        'tabular-sample': TabularSample,
        'halting-criterion-metric': HaltingCriterionMetric,
        'control-buttons': ControlButtons,
        'errors': ErrorsComponent,
        'ImageCanvas': ImageCanvas,
        'TextArea': TextArea
    },
    data: {
        apiErrors: APIErrors,
        config: undefined,
        savedAnnotation: undefined,
        item: undefined,
        stats: undefined,
        type: undefined,
        isMultiLabel: undefined,
        annotation: undefined,
        selectedLabel: undefined,

        isDone: false,
        isFirst: false,
        canLabel: true,
    },
    methods: {
        isCurrentItemLabeled() {
            const annotation = this.annotation;
            if (this.isMultiLabel) {
                return annotation?.label?.length > 0 && annotation?.label?.every((a => a.label && config.categories[a.label]));
            } else {
                return annotation?.label?.length;
            }
        },
        countUserAnnotations() {
            return this.stats.labeled + this.stats.skipped + 1
        },
        updateStatsAndProceedToNextItem: function (response) {
            this.stats = response.stats;
            this.assignNextItem();
            this.canLabel = true;
        },
        assignNextItem: function () {
            let doRemoveHead = this.item && !this.item.labelId;
            const doAssignNextItem = () => {
                this.isFirst = false;
                this.savedAnnotation = {comment: null, label: null};
                this.annotation = {comment: null, label: null};

                if (doRemoveHead) {
                    this.items.shift();
                }
                this.item = this.items[0];
                this.item.labelIndex = this.countUserAnnotations()
            };
            if (!this.items || doRemoveHead && this.items.length === 1) {
                const fetchBatchPromise = this.fetchBatch();
                fetchBatchPromise && fetchBatchPromise.then(() => {
                    doRemoveHead = false;
                    doAssignNextItem();
                });
            } else {
                doAssignNextItem();
            }

        },
        fetchBatch: function () {
            this.canLabel = false;
            if (this.isLastBatch) {
                this.isDone = true;
                this.canLabel = true;
            } else {
                let batchPromise = DKUApi.batch();
                batchPromise.then(data => {
                    this.stats = data.stats;
                    this.type = data.type;
                    this.isMultiLabel = data.isMultiLabel;
                    this.items = data.items;
                    this.canLabel = true;
                    this.isLastBatch = data.isLastBatch;
                    this.isDone = data.items.length === 0;
                    savePerIterationConfig(data.config);
                }, () => {
                    this.canLabel = true;
                });
                return batchPromise;
            }
        }
    },
    mounted: function () {
        this.assignNextItem();
        loadConfig().then(config => {
            this.config = config;
        });

    },
    // language=HTML
    template: `
        <div class="main">
            <errors></errors>
            <div v-if="config && item && !isDone" class="ongoing-training-main">
                <div class="sample-container">
                    <tabular-sample v-if="type === 'tabular'" :item="item.data"/>
                    <image-sample v-if="type === 'image'" :item="item.data"/>
                    <sound-sample v-if="type === 'sound'" :item="item.data"/>
                    <ImageCanvas v-if="type === 'image-object'"
                                 :base64source="item.data.enriched.img"
                                 :selectedLabel="selectedLabel"
                                 :objects.sync="annotation.label"
                    />
                    <TextArea v-if="type === 'text'"
                            :selectedLabel="selectedLabel"
                            :entities.sync="annotation.label"
                            :prelabels="item.prelabels"
                            :tokenizedText="item.data.raw.tokenized_text"
                    />
                    <v-popover v-if="isMultiLabel" :trigger="'hover'" :placement="'bottom'" class="shortcut-helper">
                        <img src="../../resource/img/question-sign.png" alt="Shortcuts">
                        <div slot="popover" style="text-align: left">
                            <table class="shortcuts-table">
                                <tbody>
                                    <tr>
                                        <td>
                                            <div class="keybind"><i class="fas fa-arrow-right"></i></div>
                                            /
                                            <div class="keybind">Enter</div>
                                        </td>
                                        <td>Next</td>
                                    </tr>
                                    <tr>
                                        <td>
                                            <div class="keybind"><i class="fas fa-arrow-left"></i></div>
                                        </td>
                                        <td>Back</td>
                                    </tr>
                                    <tr>
                                        <td>
                                            <div class="keybind">Space bar</div>
                                        </td>
                                        <td>Skip</td>
                                    </tr>
                                    <tr>
                                        <td>
                                            <div class="keybind">⌘</div>
                                            /
                                            <div class="keybind">shift</div>
                                            +
                                            <div class="keybind">click</div>
                                        <td>Multi-select</td>
                                    </tr>
                                    <tr>
                                        <td>
                                            <div class="keybind ng-binding">⌫</div>
                                            /
                                            <div class="keybind">␡</div>
                                            /
                                            <div class="keybind">dbl click</div>
                                        </td>
                                        <td>Delete</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </v-popover>

                </div>
                <div class="right-panel">
                    <div class="section right-panel-top">
                        <div style="display:flex; flex-direction: column; justify-content: space-between; align-items: center; margin-top: 10px; margin-bottom: 10px">
                            <div class="stat-container" v-if="stats">
                                <span class="stat"><span class="stat-count">{{stats.labeled}}</span> labeled</span>
                                <span class="stat"><span class="stat-count">{{stats.skipped}}</span> skipped</span>
                                <span class="stat"><span class="stat-count">{{stats.total}}</span> total</span>
                            </div>
                            <control-buttons :canSkip="!isDone"
                                             :isFirst="isFirst || !(stats.labeled + stats.skipped)"
                                             :isLabeled="isCurrentItemLabeled()"
                                             :currentStatus="item.status"
                            />
                            <div class="counter-container" v-if="stats">
                                <span class="stat">Sample {{item.labelIndex}} / <span class=sample-counter>{{countUserAnnotations()}}</span></span>
                            </div>
                        </div>

                        <div v-if="type != 'text'">
                            <v-popover :trigger="'hover'" :placement="'left'">
                                <div class="al-enabled-widget"
                                     :class="{ 'enabled': config.isAlEnabled }">
                                    <div class="status">
                                        <span class="icon">●</span>
                                        <span>Active learning {{config.isAlEnabled ? 'enabled' : 'unavailable'}}</span>
                                        <i class="icon-info-sign" style="flex: 1; text-align: right"></i>
                                    </div>
                                    <halting-criterion-metric
                                            v-if="config.isAlEnabled"
                                            :thresholds="config.haltingThresholds"
                                            :colors="['#2AA876','#FFD265','#CE4D45']"
                                            :currentValue="item.data.halting"></halting-criterion-metric>
                                    <div v-show="config.stoppingMessages?.length">
                                        <span class="status">
                                            <i class="icon-warning-sign" style="margin-right: 5px"></i>
                                            <span style="flex: 1">Labeling may be stopped</span>
                                        </span>
                                        <ul>
                                            <li v-for="msg in config.stoppingMessages">{{msg}}</li>
                                        </ul>
                                    </div>
                                </div>
                                <div slot="popover" style="text-align: left; max-width: 500px">
                                    <div v-if="config.isAlEnabled">
                                        <p>When Active learning is enabled so the most informative examples, with
                                           highest uncertainty scores, are displayed first. </p>
                                        <p>The colored bar is a halting criterion indicator. The indicator starts in
                                           the green area in which samples appears to be better than random sampling.
                                           In the orange zone, the sampling is not significantly better than random sampling.
                                           Red samples are the ones for which the model is almost sure, so it is probably
                                           not worth labeling them.</p>
                                        <p>The indicator is refreshed after each query generation. We advise the
                                           experimenter to retrain model and regenerate queries as often as possible
                                           even if the indicator is still in the green area.
                                        </p>
                                    </div>
                                    <div v-if="!config.isAlEnabled">
                                        <p>Active learning is disabled so samples are shown in random order.</p>
                                        <p>You need to generate a queries dataset using the query sampler recipe and
                                           define it in the webapp settings to leverage Active learning.</p>
                                    </div>

                                </div>
                            </v-popover>
                        </div>

                    </div>

                    <category-selector @label="updateStatsAndProceedToNextItem"
                                       :enabled.sync="canLabel"
                                       :stats="stats"
                                       :status="item.status"
                                       :type="type"
                                       @selectedLabel="selectedLabel = $event"
                                       :annotation="annotation"/>
                </div>
            </div>
            <div v-if="!canLabel" class="loading">Loading...</div>
            <div v-if="isDone">
                <h3>All samples are labeled</h3>
            </div>
        </div>`
});
