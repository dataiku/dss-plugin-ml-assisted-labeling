import {DKUApi} from "../dku-api.js";

const possibleKeys = new Set('abcdefghijklmnopqrstuvwxyz1234567890'.split(''));

let CategorySelector = {
    props: {
        stats: {
            type: Object,
            required: true,
        },
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
    data: () => ({
        keyToCatMapping: {},
        catToKeyMapping: {}
    }),
    methods: {
        getProgress(key) {
            if (!this.stats.labeled) {
                return 0;
            }
            return Math.round((this.stats.perLabel[key] || 0) / this.stats.labeled * 100 );
        },

        shortcutPressed: function (key) {
            this.doLabel(this.keyToCatMapping[key])
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
        },
    },
    // language=HTML
    template: `
        <div class="category-selector" v-bind:class="{ inactive: !enabled }" v-if="label">
            <div class="category-selector--categories">
                <div class="button category" v-for="(cat, i) in categories"
                     v-on:click="doLabel(cat.from)"
                     v-bind:class="{ selected: label.label && label.label.includes(cat.from) }"

                >
                    <span>{{cat.to || cat.from}}</span>
                    <code v-if="catToKeyMapping.hasOwnProperty(cat.from)" class="keybind">{{catToKeyMapping[cat.from]}}
                    </code>
                    <div class="progress-background">
                        <div class="progress" :style="{ width: getProgress(cat.from) + '%' }"></div>
                    </div>
                </div>
            </div>
            <textarea name="" id="" cols="60" rows="1" placeholder="Comments..." :disabled="!enabled"
                      ref="comments"
                      v-model="label.comment" v-on:keyup.stop></textarea>
        </div>`,
    watch: {
        "label.comment": function (nv) {
            let comments = this.$refs.comments;
            comments.style.height = "1px";
            let height = Math.min(500, 25 + comments.scrollHeight);
            comments.style.height = (height) + "px";
        }
    },
    mounted: function () {
        const unmappedCats = [];
        this.categories.forEach(cat => {
            let firstLetter = (cat.to || cat.from).trim().slice(0, 1).toLowerCase();
            if (!this.keyToCatMapping.hasOwnProperty(firstLetter)) {
                this.keyToCatMapping[firstLetter] = cat.from;
                this.catToKeyMapping[cat.from] = firstLetter;
                possibleKeys.delete(firstLetter);
            } else {
                unmappedCats.push(cat);
            }
        });
        while (unmappedCats.length && possibleKeys.size) {
            const cat = unmappedCats.pop();
            let key = possibleKeys.values().next().value;
            this.keyToCatMapping[key] = cat.from;
            this.catToKeyMapping[cat.from] = key;
            possibleKeys.delete(key);
        }
        window.addEventListener("keyup", (event) => {
            if (this.keyToCatMapping.hasOwnProperty(event.key)) {
                this.shortcutPressed(event.key);
            }
        }, false);
        this.$forceUpdate();
    },
    // language=CSS
};
export {CategorySelector}
