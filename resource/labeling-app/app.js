import {CategorySelector} from "./components/category-selector.js";
import {SoundSample} from "./components/sound-sample.js";
import {TabularSample} from "./components/tabular-sample.js";
import {ControlButtons} from "./components/control-buttons.js";
import {APIErrors, DKUApi} from "./dku-api.js";
import {ErrorsComponent} from "./components/errors.js";
import {ImageSample} from "./components/image-sample.js";
import {ImageCanvas} from "./components/image-object-sample/ImageCanvas.js";
import {config, debounce} from './components/utils/utils.js'

export default new Vue({
    el: '#app',
    components: {
        'category-selector': CategorySelector,
        'image-sample': ImageSample,
        'sound-sample': SoundSample,
        'tabular-sample': TabularSample,
        'control-buttons': ControlButtons,
        'errors': ErrorsComponent,
        'ImageCanvas': ImageCanvas
    },
    watch: {
        annotation: {
            handler: function (nv, ov) {
                this.saveImageObjectsDebounced(this.annotation)
            },
            deep: true
        }
    },
    data: {
        config: config,
        item: null,
        canLabel: true,
        stats: null,
        isDone: false,
        isFirst: false,
        type: null,
        annotation: null,
        apiErrors: APIErrors,

        annotations: null,
        selectedLabel: null,
        saveImageObjectsDebounced: null
    },
    methods: {
        isCurrentItemLabeled() {
            if (this.type === 'image-object') {
                let annotation = this.annotation;
                return !!this.item.labelId || (annotation.label && annotation.label.length > 0 || annotation.comment);
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
                    this.savedAnnotation = _.cloneDeep(annotationToSave);
                });
            }
        }, 500);
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

