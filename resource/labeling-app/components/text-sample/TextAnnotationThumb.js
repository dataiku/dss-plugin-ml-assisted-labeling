const NB_CHARS = 5;

let TextAnnotationThumb = {
    props: {
        data: Object,
        color: Array,
        isPrelabel: Boolean
    },
    data() {
        return {
            thumbTxt: null,
            hover: false,
        }
    },
    computed: {
        thumbStyle: function () {
            const style = {color: this.colorStr(this.color, 1)};
            if (!this.isPrelabel) style.background = this.colorStr(this.color, 0.3);
            if (this.isPrelabel) style.border = `2px solid ${this.colorStr(this.color, 1)}`;
            return style
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
            <span v-bind:style="thumbStyle" class="text-annotation-thumb">{{ hover ? this.data.text : thumbTxt }}</span>
        </div>    `
};

export {TextAnnotationThumb}
