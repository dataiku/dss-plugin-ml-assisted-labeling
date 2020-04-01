import {AnnotationThumb} from './AnnotationThumb.js'
import {config, UNDEFINED_COLOR} from '../utils/utils.js'

let ObjectDetectionLables = {

    props: {
        value: Array
    },
    components: {
        AnnotationThumb
    },
    data() {
        return {
            UNDEFINED_COLOR: UNDEFINED_COLOR,
            selectedLabel: null,
            categories: config.categories
        }
    },
    methods: {
        labelCaption(label) {
            return this.categories[label] ? this.categories[label].caption : (label + " (Deleted)");
        },
        labelColor(label) {
            return this.categories[label] ? this.categories[label].color : UNDEFINED_COLOR;
        },
        annotationClick(annotation) {
            this.value.forEach(a => {
                a.selected = false;
            });

            annotation.selected = !annotation.selected;
            this.$emit('input', [...this.value]);
        },
        remove(annotation) {
            this.value.splice(this.value.indexOf(annotation), 1);
        },
        color: function (label, opacity) {
            let rgb = label.color;
            return `rgb(${rgb[0]},${rgb[1]},${rgb[2]},${opacity || 1})`
        },
        toggleLabel(lbl) {
            this.selectedLabel = lbl;
            this.$emit('selectedLabel', this.selectedLabel);
        }
    },
    mounted() {
        if (this.categories) {
            this.toggleLabel(Object.keys(this.categories)[0])
        }
    },

    // language=HTML
    template: `
        <div class="wrapper">
            <div v-for="(lbl,key) in categories" class="label-config-row"
                 v-bind:class="{ 'active': selectedLabel === key }"
                 @click="toggleLabel(key)">
                <div v-bind:style="{ backgroundColor: color(lbl, 0.3) }"
                     class="color-box">
                </div>
                <div class="category">
                    <div>{{lbl.caption}}</div>
                </div>
            </div>
            <hr style="margin-top: 20px; margin-bottom: 20px ">
            <div v-if="value">

                <div v-for="a in value.filter(e=>!e.draft)" style="padding: 10px" class="annotation"
                     v-bind:class="{ selected: a.selected }"
                     @click="annotationClick(a)"
                >
                    <div style="height: 30px; width: 30px; margin-right: 30px;">
                        <AnnotationThumb :data="a" :color="labelColor(a.label)"></AnnotationThumb>
                    </div>
                    <div style="line-height: 30px">{{labelCaption(a.label)}}</div>
                    <i @click="remove(a)" class="icon-trash"/>
                </div>
            </div>
        </div>

        </div>`
};

export {ObjectDetectionLables}
