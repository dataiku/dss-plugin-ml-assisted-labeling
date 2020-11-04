import {config, UNDEFINED_COLOR} from "../utils/utils.js";

const TextArea = {
    name: 'TextArea',
    props: {
        text: String,
        objects: {
            type: Array,
            default: () => {
                return [];
            }
        },
        selectedLabel: String,
    },
    data: {
        words: {
            type: Array,
            default: () => {
                return [];
            }
        },
        selectedLabel: String,
    },

    methods: {
        splitText() {
            const text = this.text;
            const splitted_text = text.split();
            splitted_text

        },
    }

    // language=HTML
    template: `
        <div class="textarea-wrapper" ref="wrapper">
            <div class="textarea">
                <p ref="textarea" class="main-area-element">{{ text }}</p>
            </div>
            <div class="textarea__button-wrapper">
                <button @click="deleteAll()" class="main-area-element"><i class="icon-trash"></i>Delete all</button>
            </div>
        </div>`
};

export {TextArea}