import {DKUApi} from "../dku-api.js";

export let ControlButtons = {
    props: ['isFirst', 'canSkip', 'isLabeled'],
    methods: {
        back: function () {
            DKUApi.back(this.$root.sample.id).then((sample) => {
                this.$root.sample = sample;
            });
        },
        unlabeled: function () {
            DKUApi.sample().then((sample) => {
                this.$root.sample = sample;
            });
        },
        skip: function () {
            DKUApi.skip(this.$root.sample.id).then((sample) => {
                this.$root.sample = sample;
            });
        }
    },
    template: `<div class="control-buttons">
    <div class="button" v-if="!isFirst" @click="back()">Back</div>
    <div class="button" v-if="canSkip" @click="skip()">Skip</div>
    <div class="button" v-if="isLabeled" @click="unlabeled()">Next unlabeled</div>
</div>`
};
