import {DKUApi} from "../dku-api.js";
import {config, UNDEFINED_COLOR} from '../components/utils/utils.js'
import {AnnotationThumb} from "./image-object-sample/AnnotationThumb.js";

const possibleKeys = new Set('abcdefghijklmnopqrstuvwxyz1234567890'.split(''));

let CategorySelector = {
    props: {
        type: String,
        stats: {
            type: Object,
            required: true,
        },
        annotation: {
            type: Object,
            required: true,
        },
        enabled: {
            type: Boolean,
            default: true
        }
    },
    components: {
        AnnotationThumb
    },
    computed: {
        isObjectLabeling() {
            return this.type === 'image-object';
        },
    },
    directives: {
        autoExpand: {
            update: function (el) {
                el.style.height = 'inherit';
                const computed = window.getComputedStyle(el);
                const height = parseInt(computed.getPropertyValue('border-top-width'), 10)
                    + parseInt(computed.getPropertyValue('padding-top'), 10)
                    + el.scrollHeight
                    + parseInt(computed.getPropertyValue('padding-bottom'), 10)
                    + parseInt(computed.getPropertyValue('border-bottom-width'), 10);

                el.style.height = height + 'px';
            }
        }
    },

    data: () => ({
        categories: config.categories,
        keyToCatMapping: {},
        catToKeyMapping: {},
        UNDEFINED_COLOR: UNDEFINED_COLOR,
        selectedLabel: null,

    }),
    methods: {
        labelCaption(label) {
            return this.categories[label] ? this.categories[label].caption : (label + " (Deleted)");
        },
        labelColor(label) {
            return this.categories[label] ? this.categories[label].color : UNDEFINED_COLOR;
        },
        annotationClick(annotation) {
            this.annotation.label.forEach(a => {
                a.selected = false;
            });

            annotation.selected = !annotation.selected;
            this.$emit('input', [...this.annotation.label]);
        },
        remove(annotation) {
            this.annotation.label.splice(this.annotation.label.indexOf(annotation), 1);
        },
        color: function (label, opacity) {
            let rgb = label.color;
            return `rgb(${rgb[0]},${rgb[1]},${rgb[2]},${opacity || 1})`
        },
        categoryClick(lbl) {
            this.selectedLabel = lbl;
            this.$emit('selectedLabel', this.selectedLabel);
        },
        initCatToKeyMapping() {
            const unmappedCats = [];

            for (let [catKey, cat] of Object.entries(this.categories)) {
                let firstLetter = (cat.caption || catKey).trim().slice(0, 1).toLowerCase();
                if (!this.keyToCatMapping.hasOwnProperty(firstLetter)) {
                    this.keyToCatMapping[firstLetter] = catKey;
                    this.catToKeyMapping[catKey] = firstLetter;
                    possibleKeys.delete(firstLetter);
                } else {
                    unmappedCats.push(catKey);
                }
            }

            while (unmappedCats.length && possibleKeys.size) {
                const catKey = unmappedCats.pop();
                let key = possibleKeys.values().next().value;
                this.keyToCatMapping[key] = catKey;
                this.catToKeyMapping[catKey] = key;
                possibleKeys.delete(key);
            }
        },
        getProgress(key) {
            if (!this.stats.labeled) {
                return 0;
            }
            return Math.round((this.stats.perLabel[key] || 0) / this.stats.labeled * 100);
        },

        shortcutPressed: function (key) {
            if (this.isObjectLabeling) {
                this.categoryClick(this.keyToCatMapping[key]);
            } else {
                this.doLabel(this.keyToCatMapping[key])
            }
        },
        doLabel: function (c) {
            if (this.enabled) {
                this.$emit('update:enabled', false);

                this.annotation.id = this.$root.item.id;
                this.annotation.label = [c];
                DKUApi.label(this.annotation).then(labelingResponse => {
                    this.$emit('label', labelingResponse);
                })
            }
        },
    },
    // language=HTML
    template: `
        <div class="category-selector" v-bind:class="{ inactive: !enabled }" v-if="annotation">
            <div v-if="isObjectLabeling" class="category-selector__image-object-wrapper">
                <div v-for="(lbl,key) in categories" class="label-config-row"
                     v-bind:class="{ 'active': selectedLabel === key }"
                     @click="categoryClick(key)">
                    <div v-bind:style="{ backgroundColor: color(lbl, 0.3) }"
                         class="color-box">
                    </div>
                    <div class="category">
                        <div>{{lbl.caption}}</div>
                    </div>
                    <code v-if="catToKeyMapping.hasOwnProperty(key)" class="keybind">{{catToKeyMapping[key]}}</code>

                </div>
                <hr>
                <div v-if="annotation.label" class="category-selector__annotations-wrapper">
                    <div>
                        <div v-for="a in annotation.label.filter(e=>!e.draft)" class="annotation"
                             v-bind:class="{ selected: a.selected }"
                             @click="annotationClick(a)">
                            <div class="annotation-thumb-container">
                                <AnnotationThumb :data="a" :color="labelColor(a.label)"></AnnotationThumb>
                            </div>
                            <select v-model="a.label">
                                <option v-for="(lbl, key, idx) in categories" v-bind:value="key">
                                    {{ lbl.caption }}
                                </option>
                            </select>
                            <i @click="remove(a)" class="icon-trash"/>
                        </div>
                    </div>

                </div>
            </div>
            
            <div class="category-selector--categories " v-if="!isObjectLabeling">
                <div class="button category" v-for="(lbl,key) in categories"
                     v-on:click="doLabel(key)"
                     v-bind:class="{ selected: annotation.label && annotation.label.includes(key) }">
                    <span>{{lbl.caption}}</span>
                    <code v-if="catToKeyMapping.hasOwnProperty(key)" class="keybind">{{catToKeyMapping[key]}}</code>
                    <div class="progress-background">
                        <div class="progress" :style="{ width: getProgress(key) + '%' }"></div>
                    </div>
                </div>
            </div>
            <textarea name="" id="" cols="60" rows="1" placeholder="Comments..." :disabled="!enabled"
                      ref="comments"
                      v-model="annotation.comment" v-on:keyup.stop v-autoExpand class="comments"></textarea>
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

        if (this.isObjectLabeling) {
            if (this.categories) {
                this.categoryClick(Object.keys(this.categories)[0])
            }
        }

        this.initCatToKeyMapping();
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
