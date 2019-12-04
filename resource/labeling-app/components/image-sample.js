let ImageSample = {
    props: ['item'],
    computed: {
        imgSrc: function () {
            return 'data:image/png;base64, ' + this.item.enriched;
        }
    },
    // language=HTML
    template: `
        <div class="image-sample">
            <img :src="imgSrc">
        </div>`
};

export {ImageSample}
