let ImageSample = {
    props: ['sample'],
    computed: {
        imgSrc: function () {
            return 'data:image/png;base64, ' + this.sample;
        }
    },
    // language=HTML
    template: `
        <div>
            <img :src="imgSrc">
        </div>`
};

export {ImageSample}
