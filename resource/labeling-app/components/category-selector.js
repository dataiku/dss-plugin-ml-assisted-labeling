import {DKUApi} from "../dku-api.js";
import {config, UNDEFINED_COLOR} from '../components/utils/utils.js'
import {AnnotationThumb} from "./image-object-sample/AnnotationThumb.js";
import {TextAnnotationThumb} from "./text-sample/TextAnnotationThumb.js";

const possibleKeys = new Set('abcdefghijklmnopqrstuvwxyz1234567890'.split(''));

let CategorySelector = {
    props: {
        type: String,
        stats: {
            type: Object,
            required: true,
        },
        status: {type: String},
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
        AnnotationThumb,
        TextAnnotationThumb
    },
    computed: {
        isMultiLabel() {
            return this.$root.isMultiLabel;
        },
    },
    directives: {
        autoexpand: {
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
            this.selectedLabel = annotation.label;
            this.$emit('input', [...this.annotation.label]);
        },
        remove(annotation) {
            this.annotation.label.splice(this.annotation.label.indexOf(annotation), 1);
        },
        color: function (label, opacity) {
            const rgb = label.color;
            return `rgb(${rgb[0]},${rgb[1]},${rgb[2]},${opacity || 1})`
        },
        categoryClick(lbl) {
            this.selectedLabel = lbl;
            this.$emit('selectedLabel', this.selectedLabel);
            this.annotation?.label?.forEach(a => {
                if(a.selected){
                    a.label = lbl;
                }
            });
        },
        initCatToKeyMapping() {
            const unmappedCats = [];

            for (let [catKey, cat] of Object.entries(this.categories)) {
                const firstLetter = (cat.caption || catKey).trim().slice(0, 1).toLowerCase();
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
            let totalLabelBoxes = Object.values(this.stats.perLabel).reduce((a, b) => a + b, 0);
            if (totalLabelBoxes === 0){
                return 0;
            }
            if (!this.stats.labeled) {
                return 0;
            }
            return Math.round((this.stats.perLabel[key] || 0) / totalLabelBoxes * 100);
        },

        shortcutPressed: function (key) {
            if (this.isMultiLabel) {
                this.categoryClick(this.keyToCatMapping[key]);
            } else {
                this.doLabel(this.keyToCatMapping[key])
            }
        },
        doLabel: function (c) {
            if (this.enabled) {
                this.$emit('update:enabled', false);

                this.annotation.id = this.$root.item.id;
                this.annotation.labelId = this.$root.item.labelId;
                this.annotation.label = [c];
                DKUApi.label(this.annotation).then(labelingResponse => {
                    this.$emit('label', labelingResponse);
                })
            }
        },
    },

    watch: {
        "annotation.label": function (nv) {
            let selection = nv?.filter(e=>e.selected);
            if (selection?.length) {
                this.selectedLabel = selection[0].label;
            }
        },
        "label.comment": function (nv) {
            let comments = this.$refs.comments;
            comments.style.height = "1px";
            let height = Math.min(500, 25 + comments.scrollHeight);
            comments.style.height = (height) + "px";
        }
    },
    mounted: function () {
        this.initCatToKeyMapping();
        window.addEventListener("keyup", (event) => {
            if (this.keyToCatMapping.hasOwnProperty(event.key)) {
                this.shortcutPressed(event.key);
            }
        }, false);
        this.$forceUpdate();
    },
    // language=HTML
    template: `
        <div class="category-selector" :class="{ inactive: !enabled }" v-if="annotation">
            <div v-if="isMultiLabel" class="category-selector__image-object-wrapper">
                <div class="section" style="margin-bottom: 0">
                    <div class="category-selector--header">
                        <span style="  font-weight: 600; font-size: 13px;">Categories</span>
                        <span style="  font-size: 10px; color: var(--grey-lighten-3);">Select category to apply</span>
                    </div>
                    <div class="categories-container">
                        <div v-for="(lbl,key) in categories" class="right-panel-button category-button"
                             :class="{ 'active': selectedLabel === key }"
                             @click="categoryClick(key)">
                            <div :style="{ backgroundColor: color(lbl, 0.3), borderColor: color(lbl, 0.3) }"
                                 class="color-box">
                            </div>
                            <div class="category">
                                <div>{{lbl.caption}}</div>
                            </div>
                            <code v-if="catToKeyMapping.hasOwnProperty(key)"
                                  class="keybind">{{catToKeyMapping[key]}}</code>
                            <div class="progress-background"
                                v-tooltip.bottom="{content: (stats.perLabel[key] || 0) + ' label(s) - '+getProgress(key)+'% of total', enabled: getProgress(key)}">
                                <div class="progress" :style="{ width: getProgress(key) + '%' }"></div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="empty-annotations-placeholder" v-if="!annotation?.label?.filter(e=>!e.draft).length || !Object.keys(categories).length">
                    <div v-if="!Object.keys(categories).length && status !== 'SKIPPED'">
                        <div class="circle"></div>
                        <h2>Categories are not specified</h2>
                        <p>Enter a list of categories in the webapp settings</p>
                    </div>
                    <div v-else-if="status === 'SKIPPED'">
                        <i v-if="status === 'SKIPPED'" class="fas fa-forward skipped"></i>
                        <h2 v-if="status === 'SKIPPED'">Sample was skipped</h2>
                    </div>
                    <div v-else style="width: 100%;">
                        <h2 v-if="status !== 'SKIPPED'">No labels yet</h2>
                        <p v-if="isMultiLabel" style="margin: auto;">Select a category by ...</p>
                        <div class="circles-container">
                            <div style="max-width: 110px;">
                                <div class="circle cat-example"></div>
                                <span>Clicking on the categories buttons</span>
                            </div>
                            <div style="max-width: 110px;">
                                <div class="circle shortcut-example"></div>
                                <span>Using keyboard shortcuts</span>
                            </div>
                        </div>
                        <p v-if="type === 'image-object'" style="margin: auto;">... then draw a box around the target</p>
                        <p v-if="type === 'text'" style="margin: auto;">... then select a word or a group of words</p>
                    </div>
                    <div v-else-if="type === 'text'">
                        <div v-if="status !== 'SKIPPED'" class="circle"></div>
                        <h2 v-if="status !== 'SKIPPED'">No labels yet</h2>
                        <p>Select a label and select a group of words in the text.</p>
                    </div>
                    <div v-else>
                        <div v-if="status !== 'SKIPPED'" class="circle"></div>
                        <h2 v-if="status !== 'SKIPPED'">No labels yet</h2>
                        <p>Nothing selected yet.</p>
                    </div>
                </div>
                <div v-if="annotation?.label?.filter(e=>!e.draft).length"
                     class="category-selector__annotations-wrapper">
                    <div v-for="a in annotation.label.filter(e=>!e.draft)" class="annotation"
                         :class="{ selected: a.selected }"
                         @click="annotationClick(a)">
                        
                        <div class="annotation-thumb-container" v-if="type === 'image-object'" >
                            <AnnotationThumb :data="a" :color="labelColor(a.label)"></AnnotationThumb>
                        </div>
                        <div class="text-annotation-thumb-container" v-if="type === 'text'" >
                            <TextAnnotationThumb :data="a" :color="labelColor(a.label)"></TextAnnotationThumb>
                        </div>
                        
                        <div v-if="!a.label">Assign a category</div>
                        <div v-if="a.label">{{categories[a.label].caption}}</div>
                        <i @click="remove(a)" class="icon-trash"/>
                    </div>

                </div>
            </div>

            <div class="category-selector--categories" v-if="!isMultiLabel">
                <div class="empty-annotations-placeholder"
                     v-if="!Object.keys(categories).length || status === 'SKIPPED'">
                    <div v-if="!Object.keys(categories).length && status !== 'SKIPPED'">
                        <div class="circle"></div>
                        <h2>Categories are not specified</h2>
                        <p>Enter a list of categories in the webapp settings</p>
                    </div>
                    <div v-else-if="status === 'SKIPPED'">
                        <i v-if="status === 'SKIPPED'" class="fas fa-forward skipped"></i>
                        <h2 v-if="status === 'SKIPPED'">Sample was skipped</h2>
                    </div>
                </div>
                <div class="button category" v-for="(lbl,key) in categories"
                     @click="doLabel(key)"
                     :class="{ selected: annotation.label && annotation.label.includes(key) }">
                    <span>{{lbl.caption}}</span>
                    <code v-if="catToKeyMapping.hasOwnProperty(key)" class="keybind">{{catToKeyMapping[key]}}</code>
                    <div class="progress-background"
                         v-tooltip.bottom="{content: (stats.perLabel[key] || 0) + ' label(s) - '+getProgress(key)+'% of total', enabled: getProgress(key)}">
                        <div class="progress" :style="{ width: getProgress(key) + '%' }"></div>
                    </div>
                </div>
            </div>

            <textarea name="" id="" cols="60" rows="2" placeholder="Comments..." :disabled="!enabled"
                      ref="comments" style="min-height:70px"
                      v-model="annotation.comment" @keyup.stop v-autoexpand class="comments"></textarea>
        </div>`,
};
export {CategorySelector}
