import {CategorySelector} from "./components/category-selector.js";
import {SoundSample} from "./components/sound-sample.js";
import {TabularSample} from "./components/tabular-sample.js";
import {ControlButtons} from "./components/control-buttons.js";
import {APIErrors, DKUApi} from "./dku-api.js";
import {ErrorsComponent} from "./components/errors.js";
import {ImageSample} from "./components/image-sample.js";
import {ImageCanvas} from "./components/image-object-sample/ImageCanvas.js";
import {config, debounce} from './components/utils/utils.js'
import {HaltingCriterionMetric} from "./components/halting-criterion-metric.js";

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
        'ImageCanvas': ImageCanvas
    },
    data: {
        apiErrors: APIErrors,

        savedAnnotation: undefined,
        config: config,
        haltingThresholds: undefined,
        stoppingMessages: undefined,
        item: undefined,
        stats: undefined,
        type: undefined,
        annotation: undefined,
        annotations: undefined,
        selectedLabel: undefined,

        isAlEnabled: false,
        isDone: false,
        isFirst: false,
        canLabel: true,
    },
    methods: {
        isCurrentItemLabeled() {
            const annotation = this.annotation;
            if (this.type === 'image-object') {
                return annotation?.label?.filter(e => e.label).length > 0;
            } else {
                return annotation?.label?.length;
            }
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
            } else {
                let batchPromise = DKUApi.batch();
                batchPromise.then(data => {
                    this.stats = data.stats;
                    this.type = data.type;
                    this.items = data.items;
                    this.canLabel = true;
                    this.isLastBatch = data.isLastBatch;
                    this.isDone = data.items.length === 0;
                });
                return batchPromise;
            }
        }
    },
    mounted: function () {
        DKUApi.config().then(data => {
            this.isAlEnabled = data.al_enabled;
            this.haltingThresholds = data.halting_thr;
            this.stoppingMessages = data.stopping_messages;
        });


        this.assignNextItem();
    },
    // language=HTML
    template: `
        <div class="main">
            <errors></errors>
            <div v-if="item && !isDone" class="ongoing-training-main">
                <div class="sample-container">
                    <tabular-sample v-if="type === 'tabular'" :item="item.data"/>
                    <image-sample v-if="type === 'image'" :item="item.data"/>
                    <sound-sample v-if="type === 'sound'" :item="item.data"/>
                    <ImageCanvas v-if="type === 'image-object'"
                                 :base64source="item.data.enriched.img"
                                 :selectedLabel="selectedLabel"
                                 :objects.sync="annotation.label"
                    />

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
                        </div>

                        <div>
                            <v-popover :trigger="'hover'" :placement="'left'">
                                <div class="al-enabled-widget"
                                     :class="{ 'enabled': isAlEnabled }">
                                    <div class="status">
                                        <span class="icon">●</span>
                                        <span>Active learning {{isAlEnabled ? 'enabled' : 'disabled'}}</span>
                                        <i class="icon-info-sign" style="flex: 1; text-align: right"></i>
                                    </div>
                                    <halting-criterion-metric
                                            v-if="isAlEnabled"
                                            :thresholds="haltingThresholds"
                                            :colors="['#2AA876','#FFD265','#CE4D45']"
                                            :currentValue="item.data.halting"></halting-criterion-metric>
                                    <div v-show="stoppingMessages?.length">
                                        <span class="status">
                                            <i class="icon-warning-sign" style="margin-right: 5px"></i>
                                            <span style="flex: 1">Labeling may be stopped</span>
                                        </span>
                                        <ul>
                                            <li v-for="msg in stoppingMessages">{{msg}}</li>
                                        </ul>
                                    </div>
                                </div>
                                <div slot="popover">
                                    <div v-if="isAlEnabled" style="text-align: left">
                                        <p>When Active learning is enabled samples are ordered according to the
                                            uncertainty
                                            score generated by query sampler recipe.</p>
                                        <p>
                                        <div>The bar represents a halting criterion metric.</div>
                                        <div>It shows how efficient the labeling process is with Active Learning
                                            compared to random sampling.
                                        </div>
                                        <div>Being in the red zone means that your model should be retrained and
                                            labeling should continue after a queries dataset is regenerated.
                                        </div>
                                        </p>
                                    </div>
                                    <div v-if="!isAlEnabled">
                                        <p>When Active learning is disabled samples are shown in random order.</p>
                                        <p>You need to generate queries dataset using query sampler recipe to leverage
                                            Active
                                            learning.</p>
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
            <div v-if="isDone">
                <h3>All samples are labeled</h3>
            </div>
        </div>`
});
