import {config, UNDEFINED_COLOR} from "../utils/utils.js";

const SPECIAL_CHARACTERS = {
    leftWS: '([{"\\\\|,.<>\\/?]*$',
    rightWS: '^[!@#$%^&*()_+\\-=\\[\\]{};\':"\\\\|,.<>\\/?]*$',
    bothWS: '^[!@#$%^&*()_+\\-=\\[\\]{};\':"\\\\|,.<>\\/?]*$',
    noWS: '^[!@#$%^&*()_+\\-=\\[\\]{};\':"\\\\|,.<>\\/?]*$',

}

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
            let isSpecialWord = false;
            const sanitizedWordList = [];
            let currentWord = '';
            txt.split('').forEach((letter) => {
                const isWhiteSpace = letter === ' ';
                const isSpecialChar = !letter.match(/^[a-zA-Z0-9]+$/i);
                
                if (!isSpecialChar && !isWhiteSpace) {
                    sanitizedWordList.push(currentWord);
                    currentWord = '';
                    isSpecialWord = true;
                }
                if (isSpecialWord && !isWhiteSpace) {
                    sanitizedWordList.push(currentWord);
                    currentWord = '';
                    isSpecialWord = false;
                }
                currentWord += letter;
                if (letter === ' ') {
                    sanitizedWordList.push(currentWord);
                    currentWord = '';
                    isSpecialWord = false;
                }
            })
            return sanitizedWordList;
        },
    },
    computed: {
        splittedText: function () {
            return this.splitText(this.text);
        }
    },

    // language=HTML
    template: `
        <div clss="labeling-window">
            <div class="textarea-wrapper" ref="wrapper">
                <div class="textarea">
                    <div v-for="(item, index) in this.splittedText" class="word" :id="index">{{ item }}</div>
                </div>
            </div>
            <div class="textarea__button-wrapper">
                <button @click="deleteAll()" class="main-area-element"><i class="icon-trash"></i>Delete all</button>
            </div>
        </div>`
};

export {TextArea}