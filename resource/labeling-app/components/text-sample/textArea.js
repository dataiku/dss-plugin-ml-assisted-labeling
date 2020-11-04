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
        splitText(txt) {
            return txt.split(' ').map(this.sanitizeWord).reduce((x, y) => x.concat(y));
        },
        sanitizeWord(word) {
            const sanitizedWordList = [];
            if (word.match(/^[a-zA-Z0-9]+$/i)) {
                sanitizedWordList.push(word);
            } else {
                let currentWord = '';
                word.split('').forEach((letter) => {
                    if (letter.match(/^[a-zA-Z0-9]+$/i)) {
                        currentWord = currentWord + letter;
                    } else {
                        currentWord && sanitizedWordList.push(currentWord);
                        sanitizedWordList.push(letter);
                        currentWord = '';
                    }
                })
                if (currentWord) sanitizedWordList.push(currentWord);
            }
            sanitizedWordList[sanitizedWordList.length - 1] += ' ';
            return sanitizedWordList;
        },
        updateHighlightingColor(newColor) {
            this.highlightingStyleCreated && document.head.removeChild(document.head.lastChild);
            const css = document.createElement('style');
            css.setAttribute('type', 'text/css')
            css.appendChild(document.createTextNode(`#textarea *::selection {background: ${newColor};}`));
            document.head.appendChild(css);
            this.highlightingStyleCreated = true;
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
                <div class="textarea" id="textarea">
                    <span v-for="(item, index) in this.splittedText" class="word" :id="index">{{ item }}</span>
                </div>
            </div>
            <div class="textarea__button-wrapper">
                <button @click="updateHighlightingColor('red')" class="main-area-element"><i class="icon-trash"></i>Delete all</button>
            </div>
        </div>`
};

export {TextArea}