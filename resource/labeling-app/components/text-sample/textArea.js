import {config, UNDEFINED_COLOR} from "../utils/utils.js";

const SPECIAL_CHARACTERS = ['.', ',', '-', ';', ':', ]

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
            const splittedText = text.split(' ');
            const splittedTextSanitized = []
            splittedText.forEach((word) => {
                if (word.includes(''))
                splittedTextSanitized
            })

        },
        sanitizeWord(word) {
            if (word.match(/^[a-zA-Z0-9]+$/i)) {
                return [word]
            }
            const splittedWord = word.split();
            const sanitizedWordList = [];
            let currentWord = '';
            splittedWord.forEach((letter) => {
                if (letter.match(/^[a-zA-Z0-9]+$/i)) {
                    currentWord = currentWord + letter;
                } else {
                    sanitizedWordList.
                }
            })

        }
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