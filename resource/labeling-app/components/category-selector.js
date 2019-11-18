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
            if (key < 10 && key <= this.categories.length) {
                this.doLabel(this.categories[key].from)
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
                    <div v-if="i<=9" class="keybind">{{i}}</div>
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
