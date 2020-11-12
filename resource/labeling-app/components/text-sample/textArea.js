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
            const ids = e.wordsIds;
            const selected = e.selected;
            this.makeSelected(ids, category, selected)
        },
        addSelection(ids) {
            const category = config.categories[this.selectedLabel];
            this.makeSelected(ids, category, false)
        },
        getTextFromWordIds(wordIds) {
            const selectedWords = wordIds.map((x) => document.getElementById(x));
            return selectedWords.map((x) => x.innerText).reduce((x, y) => x + y);
        },
        makeSelected(ids, category, selected) {
            const color = category ? category.color : UNDEFINED_COLOR;
            const colorStrTransparent = `rgb(${color[0]},${color[1]},${color[2]}, 0.25)`;
            const colorStrOpaque = `rgb(${color[0]},${color[1]},${color[2]})`;

            const caption = category ? category.caption : UNDEFINED_CAPTION;

            const selectedWords = ids.map((x) => document.getElementById(x));
            const selectionWrapper = document.createElement('mark');
            selectionWrapper.classList.add('selection-wrapper');
            selected && selectionWrapper.classList.add('selected');
            selectionWrapper.id = this.getSelectionId(ids);
            selectionWrapper.addEventListener('dblclick', () => {
                const newEntities = this.entities.filter((x) => this.getSelectionId(ids) !== this.getSelectionId(x.wordsIds));
                this.$emit("update:entities", newEntities);
            });
            selectionWrapper.addEventListener('click', (mEvent) => {
                this.mapAndEmit((o) => {
                    if (this.getSelectionId(ids) === this.getSelectionId(o.wordsIds)) {
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
        getLabeledText(wordsIds) {
            return {
                label: this.selectedLabel,
                text: this.getTextFromWordIds(wordsIds),
                wordsIds: wordsIds,
                draft: false,
                selected: true
            }
        },
        updateObjectToObjectList(updatedObject) {
            const newObjectList = [];
            this.entities.forEach((o) => {
                newObjectList.push(this.getSelectionId(o.wordsIds) === this.getSelectionId(updatedObject.wordsIds) ? updatedObject : o)
            })
            this.emitUpdateEntities(newObjectList);
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
            const selectedWordIndexes = _.range(startSelect, endSelect + 1);
            const selectedWordIds = selectedWordIndexes.map((ind) => this.getWordId(ind));
            if (this.isLegitSelect(selectedWordIds)) {
                this.addSelection(selectedWordIds);
                this.addObjectToObjectList(this.getLabeledText(selectedWordIds));
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
        getSelectionId(wordsIds) {
            return `sel_${wordsIds ? wordsIds.join("_") : "0"}`;
        },
        isLegitSelect(selectedWordIds) {
            return !this.entities || !this.entities.some((o) => {
                return selectedWordIds.filter(value => o.wordsIds.includes(value)).length > 0;
            })
        },
        colorToCSS(color, transparency) {
            return `rgb(${color[0]},${color[1]},${color[2]}, 0.5)`;
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
        }
    },
    watch: {
        selectedLabel: function (){
            const category = config.categories[this.selectedLabel];
            const color = category ? category.color : UNDEFINED_COLOR;
            this.updateHighlightingColor(this.colorToCSS(color));
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
        this.updateHighlightingColor(this.colorToCSS(UNDEFINED_COLOR));
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