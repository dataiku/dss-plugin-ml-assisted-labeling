let AnnotationThumb = {
    props: {
        data: Object,
        color: Array
    },
    watch: {
        data: function (data) {
            this.initializeScale(data);
        }
    },
    data() {
        return {
            scale: null
        }
    },
    methods: {
        colorStr: function (original, opacity) {
            opacity = opacity || 1;
            return `rgb(${original[0]},${original[1]},${original[2]},${opacity})`
        },
        initializeScale: function (data) {
            this.scale = Math.min(this.$el.clientWidth / data.width, this.$el.clientHeight / data.height);
        }
    },
    mounted() {
        this.initializeScale(this.data);
    },
    // language=HTML
    template: `
        <div class="annotation-thumb-wrapper">
            <div v-bind:style="{ height: data.height * scale + 'px',
                width: data.width * scale + 'px',
                backgroundColor: colorStr(color, 0.3),
                borderColor: colorStr(color, 0.8)
                }"
                 class="main"
                 v-if="scale">
            </div>
        </div>    `
};

export {AnnotationThumb}
