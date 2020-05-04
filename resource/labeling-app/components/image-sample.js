let ImageSample = {
    props: ['item'],
    computed: {
        imgSrc: function () {
            return 'data:image/png;base64, ' + this.item.enriched;
        }
    },
    // language=HTML
    template: `<img class="image-sample" :src="imgSrc">`
};

export {ImageSample}
