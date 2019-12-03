let SoundSample = {
    props: ['item'],
    computed: {
        srcSound: function () {
            return 'data:audio/wav;base64, ' + this.item.enriched;
        }
    },
    // language=HTML
    template: `
        <div>
            <audio v-if="srcSound" controls="controls" autoplay="autoplay" :src="srcSound">
            </audio>
        </div>`
};

export {SoundSample}
