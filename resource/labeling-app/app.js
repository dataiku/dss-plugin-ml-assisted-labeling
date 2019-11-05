import {CategorySelector} from "./components/category-selector.js";
import {ImageSample} from "./components/image-sample.js";
import {TabularSample} from "./components/tabular-sample.js";
import {ControlButtons} from "./components/control-buttons.js";
import {DKUApi} from "./dku-api.js";

export default new Vue({
    el: '#app',
    components: {
        'category-selector': CategorySelector,
        'image-sample': ImageSample,
        'tabular-sample': TabularSample,
        'control-buttons': ControlButtons,
    },
    data: {
        config: null,
        sample: null,
    },
    mounted: function () {
        this.config = dataiku.getWebAppConfig();
        DKUApi.sample().then(sample => {
            this.sample = sample;
        });
    },
    // language=HTML
    template: `
        <div class="main" v-if="sample">
            <div v-if="!sample.is_done">
                <div class="sample-container" v-if="sample">
                    <tabular-sample v-if="sample.type === 'tabular'" :sample="sample.data"/>
                    <image-sample v-if="sample.type === 'image'" :sample="sample.data"/>
                </div>
                <control-buttons :canSkip="!sample.annotation && !sample.is_done" :isFirst="sample.is_first"
                                 :isLabeled="!!sample.annotation"/>
                <category-selector v-if="config" :categories="config.categories" :annotation="sample.annotation || {}"/>
            </div>
            <div v-if="sample.is_done">
                <h3>All samples are labeled</h3>
            </div>
            <div class="stat-container">
                <span class="stat">Labeled: {{sample.labelled}}</span>
                <span class="stat">Skipped: {{sample.skipped}}</span>
                <span class="stat">Total: {{sample.total}}</span>
            </div>
        </div>`
});
