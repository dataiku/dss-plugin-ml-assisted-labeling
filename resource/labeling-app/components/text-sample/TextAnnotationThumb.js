const NB_CHARS = 5;

let TextAnnotationThumb = {
    props: {
        data: Object,
        color: Array
    },
    data() {
        return {
            thumbTxt: null,
            hover: false,
        }
    },
    watch: {
        data: function (data) {
            this.initializeText(data);
        }
    },
    methods: {
        colorStr: function (original, opacity = 1) {
            return `rgb(${original[0]},${original[1]},${original[2]},${opacity})`
        },
        initializeText: function (data) {
            const txt = data.text;
            const truncatedTxt = txt.substring(0, NB_CHARS) + "..." + txt.substring(txt.length - NB_CHARS, txt.length)
            this.thumbTxt = txt.length <= 2*NB_CHARS ? txt : truncatedTxt;
        }
    },
    mounted() {
        this.initializeText(this.data);
    },
    // language=HTML
    template: `
        <div @mouseover="hover = true" @mouseleave="hover = false" class="annotation-thumb-wrapper">
            <span v-bind:style="{
                background: colorStr(color, 0.3),
                color: colorStr(color, 1)
                }" class="text-annotation-thumb">{{ hover ? this.data.text : thumbTxt }}</span>
        </div>    `
};

export {TextAnnotationThumb}
