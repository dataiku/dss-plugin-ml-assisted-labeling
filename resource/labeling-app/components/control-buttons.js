import {DKUApi} from "../dku-api.js";

export let ControlButtons = {
    props: ['isFirst', 'canSkip', 'isLabeled'],
    methods: {
        back: function () {
            if (!this.$root.canLabel || this.isFirst) {
                return;
            }
            DKUApi.back(this.$root.item.id).then((data) => {
                this.$root.item = data.item;
                this.$root.annotation = data.annotation;
                this.$root.savedAnnotation = _.cloneDeep(data.annotation);
                this.$root.isFirst = data.isFirst;
            });
        },
        unlabeled: function () {
            if (!this.isLabeled) {
                return
            }
            this.$root.assignNextItem();
        },
        skip: function () {
            if (!this.$root.canLabel) {
                return;
            }
            const skipLabel = {
                "dataId": this.$root.item.id,
                "labelId": this.$root.item.labelId,
                "comment": this.$root.annotation.comment
            };

            DKUApi.skip(skipLabel).then((response) => {
                this.$root.updateStatsAndProceedToNextItem(response);
            });
        }
    },
    mounted: function () {
        window.addEventListener("keyup", (event) => {
            if (event.code === 'Space') {
                this.skip();
            }
            if (event.code === 'ArrowLeft') {
                this.back();
            }
            if (event.code === 'ArrowRight') {
                this.unlabeled();
            }
        }, false);
    },
    template: `<div class="control-buttons">
    <button v-if="!isFirst" @click="back()"><span>Back</span><code class="keybind">←</code></button>
    <button v-if="canSkip" @click="skip()"><span>Skip</span><code class="keybind">Space</code></button>
    <button v-if="isLabeled" @click="unlabeled()"><span>Next unlabeled</span><code class="keybind">→</code></button>
</div>`
};
