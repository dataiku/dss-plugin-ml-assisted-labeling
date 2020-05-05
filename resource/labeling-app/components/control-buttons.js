import {DKUApi} from "../dku-api.js";

export let ControlButtons = {
    props: ['isFirst', 'canSkip', 'isLabeled'],
    data: () => {
        return {isLast: true}
    },
    methods: {
        back: function () {
            if (!this.$root.canLabel || this.isFirst) {
                return;
            }
            DKUApi.back(this.$root.item.id).then(this.processAnnotationResponce);
        },
        next: function () {
            if (!this.$root.canLabel || !this.isLabeled) {
                return;
            }
            if (this.isLast) {
                this.unlabeled();
            } else {
                DKUApi.next(this.$root.item.id).then(this.processAnnotationResponce);
            }
        },
        processAnnotationResponce: function (data) {
            this.$root.item = data.item;
            this.$root.annotation = data.annotation;
            this.$root.savedAnnotation = _.cloneDeep(data.annotation);
            this.$root.isFirst = data.isFirst;
            this.isLast = data.isLast;
        },
        first: function () {
            DKUApi.first().then(this.processAnnotationResponce);
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
                this.next();
            }
        }, false);
    },
    template: `<div class="control-buttons">
<div>
    <button :disabled="isFirst" @click="first()"><span>First</span><code class="keybind">←←</code></button>
    <button :disabled="isFirst" @click="back()"><span>Back</span><code class="keybind">←</code></button>
    <button :disabled="!canSkip" @click="skip()"><span>Skip</span><code class="keybind">Space</code></button>
    <button :disabled="!isLabeled" @click="next()"><span>Next</span><code class="keybind">→</code></button>
    <button :disabled="!isLabeled" @click="unlabeled()"><span>Next unlabeled</span><code class="keybind">→→</code></button></div>
</div>`
};
