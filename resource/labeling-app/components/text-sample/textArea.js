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
        splitText(txt) {
            return txt.split(' ').map(this.sanitizeWord).reduce((x, y) => x.concat(y));
        },
        sanitizeWord(word) {
            if (word.match(/^[a-zA-Z0-9]+$/i)) {
                return [word]
            }
            const sanitizedWordList = [];
            let currentWord = '';
            word.split('').forEach((letter) => {
                if (letter.match(/^[a-zA-Z0-9]+$/i)) {
                    currentWord = currentWord + letter;
                } else {
                    sanitizedWordList.push(currentWord);
                    sanitizedWordList.push(letter);
                    currentWord = '';
                }
            })
            if (currentWord) sanitizedWordList.push(currentWord);
            return sanitizedWordList;
        },
        splitTextInDiv() {
            const splittedText = splitText(this.text);
            splittedText.forEach((w) => {
                
                document.getElementById('textarea').
            })

        }
    },
    mounted() {

    },

    // language=HTML
    template: `
        <div class="textarea-wrapper" ref="wrapper">
            <div class="textarea">
                <p ref="textarea" id="textarea" class="main-area-element">{{ text }}</p>
            </div>
            <div class="textarea__button-wrapper">
                <button @click="deleteAll()" class="main-area-element"><i class="icon-trash"></i>Delete all</button>
            </div>
        </div>`
};

export {TextArea}