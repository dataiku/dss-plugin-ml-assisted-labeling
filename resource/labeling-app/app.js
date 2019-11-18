import {CategorySelector} from "./components/category-selector.js";
import {ImageSample} from "./components/image-sample.js";
import {SoundSample} from "./components/sound-sample.js";
import {TabularSample} from "./components/tabular-sample.js";
import {ControlButtons} from "./components/control-buttons.js";
import {DKUApi} from "./dku-api.js";

export default new Vue({
    el: '#app',
    components: {
        'category-selector': CategorySelector,
        'image-sample': ImageSample,
        'sound-sample': SoundSample,
        'tabular-sample': TabularSample,
        'control-buttons': ControlButtons,
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
    },
    methods: {
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
                });
                return batchPromise;
            }
        }
    },
    mounted: function () {
        this.config = dataiku.getWebAppConfig();
        this.assignNextItem();
    },
    // language=HTML
    template: `
        <div class="main" v-if="item">
            <div v-if="!isDone">
                <div class="sample-container">
                    <tabular-sample v-if="type === 'tabular'" :item="item.data"/>
                    <image-sample v-if="type === 'image'" :item="item.data"/>
                    <sound-sample v-if="type === 'sound'" :item="item.data"/>
                </div>
                <control-buttons :canSkip="!isDone"
                                 :isFirst="isFirst || !(stats.labeled + stats.skipped)"
                                 :isLabeled="!!item.labelId"/>
                <category-selector v-if="config" v-on:label="updateStatsAndProceedToNextItem"
                                   :categories="config.categories"
                                   v-bind:enabled.sync="canLabel"
                                   :label="label || {}"/>
            </div>
            <div v-if="isDone">
                <h3>All samples are labeled</h3>
            </div>
            <div class="stat-container">
                <span class="stat">Labeled: {{stats.labeled}}</span>
                <span class="stat">Skipped: {{stats.skipped}}</span>
                <span class="stat">Total: {{stats.total}}</span>
            </div>
        </div>`
});
