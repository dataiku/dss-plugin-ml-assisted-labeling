import {DKUApi} from "../dku-api.js";

export let ControlButtons = {
    props: ['isFirst', 'canSkip', 'isLabeled'],
    methods: {
        back: function () {
            if (!this.$root.canLabel) {
                return;
            }
            DKUApi.back(this.$root.item.id).then((data) => {
                this.$root.item = data.item;
                this.$root.label = data.label;
                this.$root.isFirst = data.isFirst;


            });
        },
        unlabeled: function () {
            this.$root.assignNextItem();
        },
        skip: function () {
            if (!this.$root.canLabel) {
                return;
            }
            const skipLabel = {
                "dataId": this.$root.item.id,
                "labelId": this.$root.item.labelId,
                "comment": this.$root.label.comment
            };

            DKUApi.skip(skipLabel).then((response) => {
                this.$root.updateStatsAndProceedToNextItem(response);
            });
        }
    },
    template: `<div class="control-buttons">
    <button v-if="!isFirst" @click="back()">Back</button>
    <button v-if="canSkip" @click="skip()">Skip</button>
    <button v-if="isLabeled" @click="unlabeled()">Next unlabeled</button>
</div>`
};
