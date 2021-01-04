import {config, UNDEFINED_COLOR, UNDEFINED_CAPTION, shortcut} from "../utils/utils.js";


const TextArea = {
    name: 'TextArea',
    props: {
        entities: {
            type: Array,
            default: () => {
                return [];
            }
        },
        selectedLabel: String,
        prelabels: {
            type: Array,
            default: () => {
                return [];
            }
        },
        tokenizedText: Object
    },
    methods: {
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
            const newRange = document.createRange();
            const startToken = this.getTokenFromStart(e.start);
            const endToken = this.getTokenFromEnd(e.end);
            if (!startToken || !endToken) return;
            const startNode = document.getElementById(this.getTokenId(startToken.id));
            const endNode = document.getElementById(this.getTokenId(endToken.id));
            newRange.setStartBefore(startNode);
            newRange.setEndAfter(endNode);
            this.makeSelected(newRange, category, e.selected, e.isPrelabel)
        },
        getTokenFromStart(start) {
            return this.tokenizedText.tokens.filter((t) => {
                return t.start === start;
            })[0]
        },
        getTokenFromEnd(end) {
            return this.tokenizedText.tokens.filter((t) => {
                return t.end === end;
            })[0]
        },
        getTextFromBoundaries(start, end) {
            return [...this.tokenizedText.text].slice(start, end).join('');
        },
        handleDblClickOnSelection(selectionId) {
            return () => {
                const newEntities = this.entities.filter(
                    (x) => selectionId !== this.getSelectionId(
                        this.getTokenFromStart(x.start).id, this.getTokenFromEnd(x.end).id));
                this.$emit("update:entities", newEntities);
            }
        },
        handleClickOnSelection(selectionId) {
            return (mEvent) => {
                if (mEvent.detail === 2) {
                    this.handleDblClickOnSelection(selectionId)(); // Firefox doesn't handle dblclick event listener
                } else {
                    this.mapAndEmit((o) => {
                        if (selectionId === this.getSelectionId(
                            this.getTokenFromStart(o.start).id, this.getTokenFromEnd(o.end).id)) {
                            o.selected = !o.selected;
                        } else {
                            o.selected = shortcut(mEvent)('multi-selection') ? o.selected : false;
                        }
                    })
                }
            }
        },
        makeSelected(range, category, selected, isPrelabel) {
            const textAreaNodes = range.startContainer.childNodes;
            const [tokenStart, tokenEnd] = [textAreaNodes[range.startOffset], textAreaNodes[range.endOffset - 1]].map((t) => {
                return this.parseTokenId(t).tokenIndex
            })
            const color = category ? category.color : UNDEFINED_COLOR;
            const colorStrTransparent = this.colorToCSS(color, 0.25);
            const colorStrOpaque = this.colorToCSS(color)

            const caption = category ? category.caption : UNDEFINED_CAPTION;

            const selectionWrapper = document.createElement('mark');
            selectionWrapper.classList.add('selection-wrapper');
            selected && selectionWrapper.classList.add('selected');
            const selectionId = this.getSelectionId(tokenStart, tokenEnd);
            selectionWrapper.id = selectionId;

            selectionWrapper.addEventListener('click', this.handleClickOnSelection(selectionId));

            if (!isPrelabel) selectionWrapper.style.background = colorStrTransparent;
            if (isPrelabel) selectionWrapper.style.border = `${selected ? 4 : 2}px solid ${colorStrOpaque}`
            range.surroundContents(selectionWrapper);

            // We place a caption at the end of the mark tag
            const captionSpan = document.createElement('span');
            captionSpan.classList.add('selected-caption');
            captionSpan.textContent = caption;
            captionSpan.style.color = colorStrOpaque
            selectionWrapper.appendChild(captionSpan);

            selected && selectionWrapper.scrollIntoView({block: "nearest", behavior: "smooth", });
        },
        getLabeledText(start, end) {
            return {
                label: this.selectedLabel,
                text: this.getTextFromBoundaries(start, end),
                start: start,
                end: end,
                draft: false,
                selected: true,//!this.selectedLabel,
                isPrelabel: false
            }
        },
        addObjectToObjectList(newObject) {
            this.emitUpdateEntities(this.entities ? this.entities.concat([newObject]) : [newObject]);
        },
        resetSelection() {
            const textarea = document.getElementById('textarea');
            textarea.innerHTML = "";
            this.tokenizedText.tokens.forEach((token, index) => {
                const newToken = document.createElement('span');
                newToken.textContent = token.text + token.whitespace;
                newToken.classList.add('token');
                newToken.id = this.getTokenId(index);
                newToken.setAttribute('data-start', token.start);
                newToken.setAttribute('data-end', token.end);
                textarea.appendChild(newToken)
            })
        },
        isLegitSelect(startToken, endToken, selectedText) {
            if (!startToken || !endToken || selectedText === startToken.whitespace) return false;
            return !this.entities || !this.entities.some((o) => {
                return startToken.start < o.start && endToken.end > o.end
            })
        },
        sanitizeBoundaryNodes(range) {
            let [startNode, endNode] = [range.startContainer, range.endContainer]
            startNode = startNode.nodeType === Node.TEXT_NODE ? startNode.parentElement : startNode;
            endNode = endNode.nodeType === Node.TEXT_NODE ? endNode.parentElement : endNode;
            const startToken = this.getTokenFromId(startNode.id);
            if (range.startOffset >= startNode.textContent.length - startToken.whitespace.length) {
                startNode = startNode.nextElementSibling;
            }
            return [startNode, endNode];
        },
        handleMouseUp() {
            const selection = document.getSelection();
            if (selection.isCollapsed || selection.toString() === "") return;
            const range = selection.getRangeAt(selection.rangeCount - 1);
            let [startNode, endNode] = this.sanitizeBoundaryNodes(range);

            const startToken = this.getTokenFromId(startNode.id);
            const endToken = this.getTokenFromId(endNode.id);

            const selectedText = range.toString();
            if (!this.isLegitSelect(startToken, endToken, selectedText)) return;

            const {charStart: charStart} = this.parseTokenId(startNode);
            const {charEnd: charEnd} = this.parseTokenId(endNode);
            if (isNaN(charStart) || isNaN(charEnd)) return;
            this.addObjectToObjectList(this.getLabeledText(charStart, charEnd));
        },

        getTokenFromId(tokenId) {
            return this.tokenizedText.tokens[this.getTokenIndex(tokenId)]
        },
        deleteAll() {
            this.emitUpdateEntities([]);
        },
        deleteSelected() {
            this.emitUpdateEntities(this.entities.filter(e => !e.selected))
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
        parseTokenId(node) {
            const splittedId = node.id.split('_');
            return {
                tokenIndex: parseInt(splittedId[1]),
                charStart: parseInt(node.dataset.start),
                charEnd: parseInt(node.dataset.end)
            }
        },
        getTokenId(n) {
            return `tok_${n}`;
        },
        getTokenIndex(tokenId) {
            return parseInt(tokenId.split('_')[1]);
        },
        init_text() {
            this.resetSelection();
            this.sanitizePrelabels();
            this.prelabels?.length && this.emitUpdateEntities(this.prelabels);
        },
        sanitizePrelabels() {
            this.prelabels.forEach((pl) => {pl.isPrelabel = true;})
        }
    },
    watch: {
        selectedLabel: function (){
            const category = config.categories[this.selectedLabel];
            const color = category ? category.color : UNDEFINED_COLOR;
            this.updateHighlightingColor(this.colorToCSS(color, 0.5));
        },
        tokenizedText: function(nv){
            this.init_text()
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
        this.init_text()
        if (this.entities) {
            this.entities.map((e) => this.addSelectionFromEntity(e));
        }
        this.updateHighlightingColor(this.colorToCSS(UNDEFINED_COLOR, 0.5));
        document.getElementById('textarea').addEventListener('click', (mEvent) => {
            !shortcut(mEvent)('multi-selection') && this.deselectAll();
        }, true);
        window.addEventListener('keyup', (event) => {
            if (shortcut(event)('delete')) {
                this.deleteSelected();
            }
        });
    },
    // language=HTML
    template: `
        <div class="labeling-window">
            <div v-bind:class="{
            'textarea-wrapper': true,
            'text-right': tokenizedText.writingSystem.direction === 'rtl',
            'text-left': tokenizedText.writingSystem.direction === 'ltr'
            }" ref="wrapper" v-on:mouseup="handleMouseUp"
                 v-bind:dir="tokenizedText.writingSystem.direction">
                <div class="textarea" id="textarea"></div>
            </div>
            <div class="textarea__button-wrapper">
                <button @click="deleteAll()" class="main-area-element delete-all-btn"><i class="icon-trash"></i>&nbsp;Delete all</button>
            </div>
        </div>`
};

export {TextArea}