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
    },
    mounted() {

    },

    // language=HTML
    template: `
        <div class="wrapper">
            

        </div>`
};

export {ObjectDetectionLables}
