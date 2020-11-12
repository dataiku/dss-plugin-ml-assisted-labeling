import {config, UNDEFINED_COLOR, UNDEFINED_CAPTION} from "../utils/utils.js";


const TextArea = {
    name: 'TextArea',
    props: {
        text: String,
        entities: {
            type: Array,
            default: () => {
                return [];
            }
        },
        selectedLabel: String,
    },
    computed: {
        splittedText: function () {
            return this.splitText(this.text);
        }
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
                        currentWord += letter;
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
        addSelectionFromEntity(e) {
            const category = config.categories[e.label];
            const selected = e.selected;
            this.makeSelected(e.startId, e.endId, category, selected)
        },
        addSelection(startId, endId) {
            const category = config.categories[this.selectedLabel];
            this.makeSelected(startId, endId, category, false)
        },
        getTextFromWordIds(startId, endId) {
            const wordIds = this.getSelectedWordsFromBoundaries(startId, endId);
            const selectedWords = wordIds.map((x) => document.getElementById(x));
            return selectedWords.map((x) => x.innerText).reduce((x, y) => x + y);
        },
        makeSelected(startId, endId, category, selected) {
            const wordsIds = this.getSelectedWordsFromBoundaries(startId, endId);
            const color = category ? category.color : UNDEFINED_COLOR;
            const colorStrTransparent = this.colorToCSS(color, 0.25);
            const colorStrOpaque = this.colorToCSS(color)

            const caption = category ? category.caption : UNDEFINED_CAPTION;

            const selectedWords = wordsIds.map((x) => document.getElementById(x));
            const selectionWrapper = document.createElement('mark');
            selectionWrapper.classList.add('selection-wrapper');
            selected && selectionWrapper.classList.add('selected');
            const selectionId = this.getSelectionId(startId, endId);
            selectionWrapper.id = selectionId;
            selectionWrapper.addEventListener('dblclick', () => {
                const newEntities = this.entities.filter(
                    (x) => selectionId !== this.getSelectionId(x.startId, x.endId));
                this.$emit("update:entities", newEntities);
            });
            selectionWrapper.addEventListener('click', (mEvent) => {
                this.mapAndEmit((o) => {
                    if (selectionId === this.getSelectionId(o.startId, o.endId)) {
                        o.selected = !o.selected;
                    } else {
                        o.selected = (mEvent.ctrlKey || mEvent.metaKey) ? o.selected : false;
                    }
                })
            });
            selectionWrapper.style.background = colorStrTransparent
            selectedWords[0].parentNode.insertBefore(selectionWrapper, selectedWords[0]);
            selectedWords.forEach((x) => selectionWrapper.appendChild(x));

            const captionSpan = document.createElement('span');
            captionSpan.classList.add('selected-caption');
            captionSpan.textContent = caption;
            captionSpan.style.color = colorStrOpaque
            selectionWrapper.appendChild(captionSpan);

        },
        getLabeledText(startId, endId) {
            return {
                label: this.selectedLabel,
                text: this.getTextFromWordIds(startId, endId),
                startId: startId,
                endId: endId,
                draft: false,
                selected: true
            }
        },
        addObjectToObjectList(newObject) {
            this.emitUpdateEntities(this.entities ? this.entities.concat([newObject]) : [newObject]);
        },
        resetSelection() {
            const textarea = document.getElementById('textarea');
            textarea.innerHTML = "";
            this.splittedText.forEach((word, index) => {
                const newWord = document.createElement('span');
                newWord.textContent = word;
                newWord.classList.add('word');
                newWord.id = this.getWordId(index);
                textarea.appendChild(newWord)
            })
        },
        handleMouseUp() {
            const selection = document.getSelection();
            if (selection.isCollapsed) return;
            const focusWord = this.getWordIndex(selection.focusNode.parentElement.id);
            const anchorWord = this.getWordIndex(selection.anchorNode.parentElement.id);
            let startSelect, endSelect;
            [startSelect, endSelect] = _.sortBy([anchorWord, focusWord]);
            if (this.isLegitSelect(startSelect, endSelect)) {
                this.addSelection(startSelect, endSelect);
                this.addObjectToObjectList(this.getLabeledText(startSelect, endSelect));
            }
        },
        deleteAll() {
            this.emitUpdateEntities([]);
        },
        deselectAll() {
            if (!this.entities) return;
            const newObjectList = _.cloneDeep(this.entities)
            newObjectList.map((o) => {o.selected = false})
            this.emitUpdateEntities(newObjectList);
        },
        getSelectionId(startId, endId) {
            return `sel_${startId}_${endId}`;
        },
        isLegitSelect(startId, endId) {
            return !this.entities || !this.entities.some((o) => {
                return _.intersection(_.range(startId, endId + 1), _.range(o.startId, o.endId + 1)).length > 0;
            })
        },
        colorToCSS(color, transparency=1) {
            return `rgb(${color[0]},${color[1]},${color[2]}, ${transparency})`;
        },
        mapAndEmit(fn) {
            const newObjectList = _.cloneDeep(this.entities);
            newObjectList.map(fn);
            this.emitUpdateEntities(newObjectList);

        },
        emitUpdateEntities(newObjects) {
            this.$emit("update:entities", newObjects);
        },
        getWordId(n) {
            return `w_${n}`;
        },
        getWordIndex(wordId) {
            return parseInt(wordId.split('_')[1]);
        },
        getSelectedWordsFromBoundaries(startId, endId) {
            return _.range(startId, endId + 1).map(this.getWordId);
        }
    },
    watch: {
        selectedLabel: function (){
            const category = config.categories[this.selectedLabel];
            const color = category ? category.color : UNDEFINED_COLOR;
            this.updateHighlightingColor(this.colorToCSS(color, 0.5));
        },
        text: function(nv){
            this.resetSelection();
        },
        entities: {
            handler(nv) {
                if (!nv) {
                    return;
                }
                this.resetSelection();
                nv.map(this.addSelectionFromEntity);
            },
            deep: true
        }
    },
    mounted() {
        this.resetSelection();
        if (this.entities) {
            this.entities.map((e) => this.addSelectionFromEntity(e));
        }
        this.updateHighlightingColor(this.colorToCSS(UNDEFINED_COLOR, 0.5));
        document.getElementById('textarea').addEventListener('click', (mEvent) => {
            !(mEvent.ctrlKey || mEvent.metaKey) && this.deselectAll();
        }, true);
    },
    // language=HTML
    template: `
        <div clss="labeling-window">
            <div class="textarea-wrapper" ref="wrapper" v-on:mouseup="handleMouseUp">
                <div class="textarea" id="textarea"></div>
            </div>
            <div class="textarea__button-wrapper">
                <button @click="deleteAll()" class="main-area-element"><i class="icon-trash"></i>&nbsp;Delete all</button>
            </div>
        </div>`
};

export {TextArea}