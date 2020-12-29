import {DKUApi} from "../dku-api.js";
import {shortcut} from "./utils/utils.js";

export let ControlButtons = {
    props: ['isFirst', 'canSkip', 'isLabeled', 'currentStatus'],
    data: () => {
        return {isLast: true}
    },
    computed: {
        annotationToSave:function(){
            const label = this.$root.annotation?.label;
            return {
                comment: this.$root.annotation.comment || null,
                label: label?.length ? label : null
            };
        },
        isMultiLabel() {
            return this.$root.isMultiLabel;
        },
        isDirty: function () {
            if (this.isMultiLabel) {
                return !_.isEqual(this.annotationToSave, this.$root.savedAnnotation)
            } else {
                return false;
            }
        },
    },
    methods: {
        back: function () {
            if (!this.$root.canLabel || this.isFirst) {
                return;
            }
            DKUApi.back(this.$root.item.labelId).then(this.processAnnotationResponce);
        },

        saveIfRequired: function () {
            return new Promise((resolve, reject) => {
                if (this.isMultiLabel) {
                    const annotationToSave = this.annotationToSave;
                    if (this.isSaveRequired()) {
                        if (!_.isEqual(annotationToSave.comment, this.$root.savedAnnotation.comment) && this.$root.item.status === 'SKIPPED') {
                            this.skip().then(resolve);
                        } else {
                            DKUApi.label({...annotationToSave, ...{id: this.$root.item.id}}).then(labelingResponse => {
                                this.$root.stats = labelingResponse.stats;
                                resolve();
                            });
                        }
                    } else {
                        resolve();
                    }
                } else {
                    resolve();
                }
            })
        },
        next: function () {
            if (!this.$root.canLabel || (!this.currentStatus && !this.isLabeled)) {
                return;
            }
            this.saveIfRequired().then(() => {
                if (this.isLast) {
                    this.unlabeled(true);
                } else {
                    DKUApi.next(this.$root.item.labelId).then(this.processAnnotationResponce);
                }
            });
        },

        isSaveRequired(){
            return this.isDirty && this.isLabeled;
        },
        processAnnotationResponce: function (data) {
            this.$root.item = data.item;
            this.$root.annotation = data.annotation;
            this.$root.savedAnnotation = _.cloneDeep(data.annotation);
            this.$root.isFirst = data.isFirst;
            this.isLast = data.isLast;
        },
        first: function () {
            if (!this.$root.canLabel || this.isFirst) {
                return;
            }
            DKUApi.first().then(this.processAnnotationResponce);
        },
        unlabeled: function (force=false) {
            if ((!this.currentStatus || !this.$root.item.labelId) && !force) {
                return;
            }
            this.$root.assignNextItem();
            this.isLast = true;
        },
        skip: function () {
            return new Promise((resolve, reject) => {
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
                    resolve(response);
                });
            });
        }
    },
    mounted: function () {
        window.addEventListener("keyup", (event) => {
            if (shortcut(event)('back')) {
                this.back();
            }
            if (shortcut(event)('next')) {
                this.next();
            }
            if (shortcut(event)('skip')) {
                this.skip();
            }
            if (shortcut(event)('first')) {
                this.first();
            }
            if (shortcut(event)('last')) {
                this.unlabeled();
            }
        }, false);
    },
    template: `<div class="control-buttons">
    <button class="right-panel-button" :disabled="isFirst" @click="first()"><span>first</span><code class="keybind"><i class="fas fa-arrow-up"></i></code></i></button>
    <button class="right-panel-button" :disabled="isFirst" @click="back()"><span>back</span><code class="keybind"><i class="fas fa-arrow-left"></i></code></button>
    <button class="right-panel-button skip-button" @click="skip()"><span>skip</span><code class="keybind">TAB</code></button>
    <v-popover :trigger="'hover'" :placement="'bottom'">
        <button class="right-panel-button" @click="next()" :disabled="!isLabeled && currentStatus !== 'SKIPPED'"><span>{{isSaveRequired() ? 'save & next' : 'next'}}</span><code class="keybind"><i class="fas fa-arrow-right"></i></code></button>
        <div slot="popover">
            Alternative hotkey: <code class="keybind" style="vertical-align: baseline">Space</code>
        </div>
    </v-popover>
    <button class="right-panel-button" :disabled="!$root.item.labelId" @click="unlabeled()" style="margin-right: 0"><span>Last</span><code class="keybind"><i class="fas fa-arrow-down"></i></code></i></button></div>
`
};
