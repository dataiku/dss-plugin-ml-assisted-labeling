import {DKUApi} from "../dku-api.js";

let CategorySelector = {
    props: {
        categories: {
            type: Array,
            required: true,
        },
        label: {
            type: Object,
            required: true,
        },
        enabled: {
            type: Boolean,
            default: true
        }
    },
    data: () => ({}),
    methods: {
        shortcutPressed: function (key) {
            if (key <= this.categories.length) {
                if (key === 0 && this.categories.length === 10) {
                    this.doLabel(this.categories[10].from)
                } else {
                    this.doLabel(this.categories[key - 1].from)
                }
            }
        },
        doLabel: function (c) {
            if (this.enabled) {
                this.$emit('update:enabled', false);

                this.label.id = this.$root.item.id;
                this.label.label = [c];
                DKUApi.label(this.label).then(labelingResponse => {
                    this.$emit('label', labelingResponse);
                })

            }
        }
    },
    // language=HTML
    template: `
        <div class="category-selector" v-bind:class="{ inactive: !enabled }" v-if="label">
            <div class="category-selector--categories">
                <div class="button" v-for="(cat, i) in categories"
                     v-on:click="doLabel(cat.from)"
                     v-bind:class="{ selected: label.label && label.label.includes(cat.from) }"

                >
                    <span>{{cat.to || cat.from}}</span>
                    <div class="keybind">{{i+1}}</div>
                </div>
            </div>
            <textarea name="" id="" cols="60" rows="3" placeholder="Comments..." :disabled="!enabled"
                      v-model="label.comment"></textarea>
        </div>`,
    mounted: function () {
        window.addEventListener("keydown", (event) => {
            if (event.code.startsWith("Digit")) {
                this.shortcutPressed(parseInt(event.key));
            }
        }, true);
    },
    // language=CSS
};
export {CategorySelector}
