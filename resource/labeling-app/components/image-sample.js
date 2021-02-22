let ImageSample = {
    props: {
        item: Object,
        labels: {
            type: Array,
            default: () => {
                return [];
            }
        },
        selectedLabel: String,
    },
    computed: {
        imgSrc: function () {
            return 'data:image/png;base64, ' + this.item.enriched;
        }
    },
    methods: {
        getLabeledText() {
            return {
                label: this.selectedLabel
            }
        }
    },
    watch: {
        selectedLabel: function () {
            if (this.labels && this.labels.filter((l) => l.label === this.selectedLabel).length) return;
            const newLabels = this.labels ? this.labels.concat([this.getLabeledText()]) : [this.getLabeledText()];
            this.$emit("update:labels", newLabels);
        },
        labels: {
            handler(nv) {
                if (!nv) {
                    return;
                }
            },
            deep: true
        }
    },
    // language=HTML
    template: `<img class="image-sample" :src="imgSrc">`
};

export {ImageSample}
