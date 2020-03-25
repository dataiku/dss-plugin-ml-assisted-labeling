import {CategorySelector} from "./components/category-selector.js";
import {SoundSample} from "./components/sound-sample.js";
import {TabularSample} from "./components/tabular-sample.js";
import {ControlButtons} from "./components/control-buttons.js";
import {APIErrors, DKUApi} from "./dku-api.js";
import {ErrorsComponent} from "./components/errors.js";
import {ImageSample} from "./components/image-sample.js";
import {ImageObjectSample} from "./components/image-object-sample/ImageObjectSample.js";
import {ObjectDetectionLables} from "./components/image-object-sample/ObjectDetectionLables.js";
import {ImageCanvas} from "./components/image-object-sample/ImageCanvas.js";
import {stringToRgb} from './components/utils/utils.js'

export default new Vue({
    el: '#app',
    components: {
        'category-selector': CategorySelector,
        'image-sample': ImageSample,
        'image-object-sample': ImageObjectSample,
        'sound-sample': SoundSample,
        'tabular-sample': TabularSample,
        'control-buttons': ControlButtons,
        'errors': ErrorsComponent,
        'ObjectDetectionLables': ObjectDetectionLables,
        'ImageCanvas': ImageCanvas
    },
    data: {
        config: null,
        item: null,
        canLabel: true,
        stats: null,
        isDone: false,
        isFirst: false,
        type: null,
        label: null,
        apiErrors: APIErrors,

        //TODO remove mocks
        annotations: null,
        labelConfig: {
            player_one: {caption: "Player team 1", color: stringToRgb("player_one")},
            player_two: {caption: "Player team 2", color: stringToRgb("player_two")},
            ball: {caption: "Ball", color: stringToRgb("ball")}
        },
        imgSource: "https://static01.nyt.com/images/2020/02/27/sports/27EmptyStadium-top/27EmptyStadium-top-superJumbo.jpg?quality=90&auto=webp",
        // imgSource: "https://img-19.ccm2.net/A32teLO0gaI8gWItzOYPOXfzMP0=/0129df8cd66948a9982deae91b956987/ccm-faq/UdNoIiE2Mc0cL0hXoYsExsy60V-2-gimp-s-.png",
        // imgSource: "https://upload.wikimedia.org/wikipedia/commons/0/0f/Eiffel_Tower_Vertical.JPG",
        selectedLabel: null

    },
    methods: {
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
                this.label = {};
                this.isFirst = false;

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
        this.annotations = [
            // {top: 682, left: 1024, width: 574, height: 200, label: 'player_team2'},
            // {top: 1500, left: 123, width: 300, height: 800, label: 'ball'},
            {
                "id": "680fd82b-2e1d-4365-8b97-060607b109fa",
                "label": "ball",
                "left": 448,
                "top": 244,
                "width": 28,
                "height": 32
            },
        ];
        this.config = dataiku.getWebAppConfig();
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
                    <ImageCanvas :v-if="type === 'image-object'"
                                 :img="imgSource"
                                 :selectedLabel="selectedLabel"
                                 :labelConfig="labelConfig"
                                 v-model="annotations"/>

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
                                         :isLabeled="!!item.labelId"/>
                    </div>
                    <category-selector v-if="config && type !== 'image-object'"
                                       v-on:label="updateStatsAndProceedToNextItem"
                                       :categories="config.categories"
                                       :stats="stats"
                                       v-bind:enabled.sync="canLabel"
                                       :label="label || {}"/>
                    <ObjectDetectionLables :labelConfig="labelConfig" v-on:selectedLabel="labelSelected"
                                           v-if="type === 'image-object'"
                                           v-model="annotations">
                    </ObjectDetectionLables>

                </div>
            </div>
            <div v-if="isDone">
                <h3>All samples are labeled</h3>
            </div>

        </div>`
});

