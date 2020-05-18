import {DKUApi} from "../dku-api.js";

export let ControlButtons = {
    props: ['isFirst', 'canSkip', 'isLabeled'],
    data: () => {
        return {isLast: true}
    },
    computed: {
        annotationToSave:function(){
            let label = this.$root.annotation?.label && this.$root.annotation.label.filter(e => e.label).map(a => {
                return {top: a.top, left: a.left, label: a.label, width: a.width, height: a.height}
            });
            return {
                comment: this.$root.annotation.comment || null,
                label: label?.length ? label : null
            };
        },
        isDirty: function () {
            if (this.$root.type === 'image-object') {
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
                if (this.$root.type === 'image-object') {
                    const annotationToSave = this.annotationToSave;
                    if (this.isDirty) {
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
            if (!this.$root.canLabel || !this.isLabeled) {
                return;
            }
            this.saveIfRequired().then(() => {
                if (this.isLast) {
                    this.unlabeled();
                } else {
                    DKUApi.next(this.$root.item.labelId).then(this.processAnnotationResponce);
                }
            });
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
            if (event.code === 'Enter') {
                this.skip();
            }
            if (event.code === 'ArrowLeft') {
                this.back();
            }
            if (event.code === 'ArrowRight' || event.code === 'Space') {
                this.next();
            }
        }, false);
    },
    template: `<div class="control-buttons">
    <button class="right-panel-button" :disabled="isFirst" @click="first()"><i class="fas fa-step-backward"></i></button>
    <button class="right-panel-button" :disabled="isFirst" @click="back()"><i class="fas fa-chevron-left"></i><span>back</span><code class="keybind"><i class="fas fa-arrow-left"></i></code></button>
    <button class="right-panel-button" @click="skip()"><span>skip</span><code class="keybind">Enter</code></button>
    <v-popover :trigger="'hover'" :placement="'bottom'">
        <button class="right-panel-button" @click="next()" :disabled="!isLabeled"><span>{{isDirty ? 'save & next' : 'next'}}</span><code class="keybind"><i class="fas fa-arrow-right"></i></code></button>
        <div slot="popover">
            Alternative hotkey: <code class="keybind" style="vertical-align: baseline">Space</code>
        </div>
    </v-popover>
    <button class="right-panel-button" :disabled="!$root.item.labelId" @click="unlabeled()" style="margin-right: 0"><i class="fas fa-step-forward"></i></button></div>
`
};
