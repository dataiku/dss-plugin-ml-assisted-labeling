import {AnnotationThumb} from './AnnotationThumb.js'

let ObjectDetectionLables = {

    props: {
        labelConfig: Object,
        value: Array
    },
    components: {
        AnnotationThumb
    },
    data() {
        return {
            uiData: {selectedLabel: null}
        }
    },
    methods: {
        annotationClick(annotation) {
            this.value.forEach(a => {
                a.selected = false;
            });

            annotation.selected = !annotation.selected;
            console.log(this.value);
            this.$emit('input', this.value);
        },
        remove(annotation) {
            this.value.splice(this.value.indexOf(annotation), 1);
        },
        color: function (original, opacity) {
            opacity = opacity || 1;
            return `rgb(${original[0]},${original[1]},${original[2]},${opacity})`
        },
        toggleLabel(lbl) {
            if (this.uiData.selectedLabel === lbl) {
                this.uiData.selectedLabel = null;
            } else {
                this.uiData.selectedLabel = lbl;
            }
            this.$emit('selectedLabel', this.uiData.selectedLabel);
        }
    },
    mounted() {
        let labels = Object.keys(this.labelConfig);
        if (labels.length) {
            this.toggleLabel(labels[0])
        }
    },

    // language=HTML
    template: `
        <div class="wrapper" v-if="value">
            <div v-for="(lbl,key) in labelConfig" class="label-config-row"
                 v-bind:class="{ 'active': uiData.selectedLabel === key }"
                 @click="toggleLabel(key)">
                <div v-bind:style="{ backgroundColor: color(lbl.color, 0.3) }"
                     class="color-box">
                </div>
                <div class="category">
                    <div>{{lbl.caption}}</div>
                </div>
            </div>
            <hr style="margin-top: 20px; margin-bottom: 20px ">
            <div v-for="a in value.filter(e=>!e.draft)" style="padding: 10px" class="annotation"
                 v-bind:class="{ selected: a.selected }"
                 @click="annotationClick(a)"
            >
                <div style="height: 30px; width: 30px; margin-right: 30px;">
                    <AnnotationThumb :data="a" :color="labelConfig[a.label].color"></AnnotationThumb>
                </div>
                <div style="line-height: 30px">{{labelConfig[a.label].caption}}</div>
                <i @click="remove(a)" class="icon-trash"/>
            </div>
        </div>`
};

export {ObjectDetectionLables}
