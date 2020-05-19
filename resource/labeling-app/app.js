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
    watch: {
        annotation: {
            handler: function () {
                this.annotation.label &&  this.saveImageObjectsDebounced(this.annotation)
            },
            deep: true
        }
    },
    data: {
        config: config,
        haltingThresholds: null,
        item: null,
        canLabel: true,
        stats: null,
        isDone: false,
        isFirst: false,
        type: null,
        annotation: null,
        apiErrors: APIErrors,
        currentALColor: null,
        currentALValue: null,
        annotations: null,
        selectedLabel: null,
        saveImageObjectsDebounced: null
    },
    methods: {
        isCurrentItemLabeled() {
            if (this.type === 'image-object') {
                let annotation = this.annotation;
                return !!this.item.labelId || (annotation.label && annotation.label.length > 0);
            } else {
                return !!this.item.labelId;
            }
        },
        labelSelected(selectedLabel) {
            this.selectedLabel = selectedLabel;
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
        this.saveImageObjectsDebounced = debounce.call(this, () => {
            let mapLabelToSaveObject = a => {
                return {top: a.top, left: a.left, label: a.label, width: a.width, height: a.height}
            };
            let annotation = this.annotation;
            let annotationToSave = {
                comment: annotation.comment,
                label: annotation.label && annotation.label.map(mapLabelToSaveObject)
            };
            if (!_.isEqual(annotationToSave, this.savedAnnotation)) {
                let annotationData = {...annotationToSave, ...{id: this.item.id}};
                console.log("SAVE", annotationData);
                DKUApi.label(annotationData).then(labelingResponse => {
                    this.$emit('label', labelingResponse);
                    this.stats = labelingResponse.stats;
                    this.savedAnnotation = _.cloneDeep(annotationToSave);
                });
            }
        }, 500);


        DKUApi.config().then(data => {
            this.isAlEnabled = data.al_enabled;
            this.currentALValue = data.halting_score;
            this.haltingThresholds = data.halting_thresholds;
        });


        this.assignNextItem();
    },
    // language=HTML
    template: `
        <div class="main">
            <errors></errors>
            <div v-if="item && !isDone" class="ongoing-training-main">
                <div class="sample-container">
                    <v-popover :trigger="'hover'"
                               style="transform: translateX(-50%); position: absolute; top: 10px; left: 50%; border-radius: 4px">
                        <div class="al-enabled-widget"
                             :style="{backgroundColor: isAlEnabled && currentALColor}"
                             v-bind:class="{ 'enabled': isAlEnabled }">
                            <span>●</span> Active learning {{isAlEnabled ? 'enabled' : 'disabled'}}
                        </div>
                        <div slot="popover" class="al-status-popover">
                            <div v-if="isAlEnabled">
                                <p>When Active learning is enabled samples are ordered according to the uncertainty
                                    score generated by query sampler recipe</p>
                                <p>Efficiency of labeling using Active learning can be controlled by the halting
                                    metric:</p>
                                <halting-criterion-metric
                                        :thresholds="haltingThresholds"
                                        :colors="['#2AA876','#FFD265','#F19C65','#CE4D45']"
                                        :currentValue="currentALValue"
                                        @currentColor="currentALColor=$event"></halting-criterion-metric>
                            </div>
                            <div v-if="!isAlEnabled">
                                <p>When Active learning is disabled samples are shown in random order</p>
                                <p>You need to generate queries dataset using query sampler recipe to leverage Active
                                    learning.</p>
                            </div>
                        </div>
                    </v-popover>
                    <tabular-sample v-if="type === 'tabular'" :item="item.data"/>
                    <image-sample v-if="type === 'image'" :item="item.data"/>
                    <sound-sample v-if="type === 'sound'" :item="item.data"/>
                    <ImageCanvas v-if="type === 'image-object'"
                                 :base64source="item.data.enriched"
                                 :selectedLabel="selectedLabel"
                                 v-bind:objects.sync="annotation.label"
                    />
                    <!--                                 v-on:update:objects="saveImageObjectsDebounced"-->

                </div>
                <div class="right-pannel">
                    <div class="right-pannel-top">
                        <div class="stat-container" v-if="stats">
                            <span class="stat"><span class="stat-count">{{stats.total}}</span> samples</span>
                            <span class="stat"><span class="stat-count">{{stats.labeled}}</span> labeled</span>
                            <span class="stat"><span class="stat-count">{{stats.skipped}}</span> skipped</span>
                        </div>
                        <control-buttons :canSkip="!isDone"
                                         :isFirst="isFirst || !(stats.labeled + stats.skipped)"
                                         :isLabeled="isCurrentItemLabeled()"/>
                    </div>

                    <category-selector v-on:label="updateStatsAndProceedToNextItem"
                                       v-bind:enabled.sync="canLabel"
                                       :stats="stats"
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

