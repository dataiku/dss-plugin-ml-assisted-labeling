import {config, shortcut, UNDEFINED_CAPTION, UNDEFINED_COLOR} from "../utils/utils.js";


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
            const [startToken, endToken] = [this.getTokenFromStart(e.start), this.getTokenFromEnd(e.end)];
            if (!startToken || !endToken) return;
            const [startNode, endNode] = [startToken, endToken].map(this.getNodeFromToken);

            const newRange = document.createRange();
            newRange.setStartBefore(startNode);
            newRange.setEndAfter(endNode);
            newRange.startToken = startToken;
            newRange.endToken = endToken;
            this.makeSelected(newRange, config.categories[e.label], e.selected, e.isPrelabel)
        },
        handleSimpleClickOnSelection(selectionId) {
            return (mEvent) => {
                this.mapAndEmit((o) => {
                    if (selectionId === this.getSelectionId(
                        this.getTokenFromStart(o.start).id, this.getTokenFromEnd(o.end).id)) {
                        o.selected = !o.selected;
                    } else {
                        o.selected = shortcut(mEvent)('multi-selection') ? o.selected : false;
                    }
                })
            }
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
                    this.handleSimpleClickOnSelection(selectionId)(mEvent);
                }
            }
        },
        getCategoryColor(category, isTransparent=false) {
            const color = category ? category.color : UNDEFINED_COLOR;
            return this.colorToCSS(color, isTransparent ? 0.25 : 1);
        },
        getCategoryCaption(category) {
            return category ? category.caption : UNDEFINED_CAPTION;
        },
        createSelectionWrapper(startToken, endToken, category, selected, isPrelabel) {
            const selectionWrapper = document.createElement('mark');
            selectionWrapper.classList.add('selection-wrapper');
            if (selected) selectionWrapper.classList.add('selected');
            const selectionId = this.getSelectionId(startToken.id, endToken.id);
            selectionWrapper.id = selectionId;
            selectionWrapper.addEventListener('click', this.handleClickOnSelection(selectionId));
            if (isPrelabel) {
                selectionWrapper.style.border = `${selected ? 4 : 2}px solid ${this.getCategoryColor(category)}`
            } else {
                selectionWrapper.style.background = this.getCategoryColor(category, true);
            }
            return selectionWrapper;
        },
        createSelectionCaption(category) {
            const selectionCaption = document.createElement('span');
            selectionCaption.classList.add('selected-caption');
            selectionCaption.textContent = this.getCategoryCaption(category);
            selectionCaption.style.color = this.getCategoryColor(category);
            return selectionCaption
        },
        makeSelected(range, category, selected, isPrelabel) {
            const startToken = range.startToken;
            const endToken = range.endToken;

            const selectionWrapper = this.createSelectionWrapper(startToken, endToken, category, selected, isPrelabel);
            range.surroundContents(selectionWrapper);

            const selectionCaption = this.createSelectionCaption(category);
            selectionWrapper.appendChild(selectionCaption);

            selected && selectionWrapper.scrollIntoView({block: "nearest", behavior: "smooth"});
        },
        getLabeledText(start, end) {
            return {
                label: this.selectedLabel,
                text: this.getTextFromBoundaries(start, end),
                start: start,
                end: end,
                draft: false,
                selected: true,
                isPrelabel: false
            }
        },
        addObjectToObjectList(newObject) {
            this.emitUpdateEntities(this.entities ? this.entities.concat([newObject]) : [newObject]);
        },
        createToken(token, index) {
            const tokenDOM = document.createElement('span');
            tokenDOM.textContent = token.text + token.whitespace;
            tokenDOM.classList.add('token');
            tokenDOM.id = this.getTokenId(index);
            tokenDOM.setAttribute('data-start', token.start);
            tokenDOM.setAttribute('data-end', token.end);
            tokenDOM.setAttribute('data-is-selectable', token.text.trim().length > 0);
            return tokenDOM
        },
        resetSelection() {
            const textarea = document.getElementById('textarea');
            textarea.innerHTML = "";
            this.tokenizedText.tokens.forEach((token, index) => {
                textarea.appendChild(this.createToken(token, index))
            })
        },
        isLegitSelect() {
            const selection = document.getSelection();
            if (selection.isCollapsed || selection.toString() === "") return;
            if (selection.rangeCount > 1 && selection.getRangeAt(0).toString().length > 0) return;

            let [startNode, endNode] = this.sanitizeBoundaryNodes(selection);
            if (!startNode || !endNode) return;

            const nodesComparison = startNode.compareDocumentPosition(endNode);
            if (![0, 4].includes(nodesComparison)) return;

            const [startToken, endToken] = [this.getTokenFromNode(startNode), this.getTokenFromNode(endNode)];
            if (!startToken || !endToken) return;

            return !this.entities || !this.entities.some((o) => {
                return startToken.start < o.start && endToken.end > o.end
            })
        },
        sanitizeBoundaryNodes(selection) {
            const range = selection.getRangeAt(selection.rangeCount - 1);
            let [startNode, endNode] = [range.startContainer, range.endContainer];

            startNode = startNode.nodeType === Node.TEXT_NODE ? startNode.parentElement : startNode;
            endNode = endNode.nodeType === Node.TEXT_NODE ? endNode.parentElement : endNode;

            while(startNode.getAttribute('data-is-selectable') === 'false') {
                startNode = startNode.nextElementSibling;
            }

            while (endNode.getAttribute('data-is-selectable') === 'false') {
                endNode = endNode.previousElementSibling;
            }

            const startToken = this.getTokenFromNode(startNode);
            if (!startToken || range.toString() === startToken.whitespace) {
                startNode = null;
            } else if (range.startOffset >= startNode.textContent.length - startToken.whitespace.length) {
                startNode = startNode.nextElementSibling; // Compatibility with Firefox
            }
            return [startNode, endNode];
        },
        getBoundaryNodes() {
            const selection = document.getSelection();
            return this.sanitizeBoundaryNodes(selection);
        },
        handleMouseUp() {
            if (!this.isLegitSelect()) return;
            let [startNode, endNode] = this.getBoundaryNodes();

            const charStart = parseInt(startNode.dataset.start);
            const charEnd = parseInt(endNode.dataset.end);
            if (isNaN(charStart) || isNaN(charEnd)) return;
            this.addObjectToObjectList(this.getLabeledText(charStart, charEnd));
        },
        deleteAll() {
            this.emitUpdateEntities([]);
        },
        deleteSelected() {
            this.emitUpdateEntities(this.entities.filter(e => !e.selected))
        },
        deselectAll() {
            if (!this.entities) return;
            this.mapAndEmit((o) => {o.selected = false})
        },
        colorToCSS(color, opacity=1) {
            return `rgb(${color[0]},${color[1]},${color[2]}, ${opacity})`;
        },
        mapAndEmit(fn) {
            const newObjectList = _.cloneDeep(this.entities);
            newObjectList.map(fn);
            this.emitUpdateEntities(newObjectList);
        },
        emitUpdateEntities(newObjects) {
            this.$emit("update:entities", newObjects);
        },
        init_text() {
            this.resetSelection();
            this.sanitizePrelabels();
            this.prelabels?.length && this.emitUpdateEntities(this.prelabels);
        },
        sanitizePrelabels() {
            this.prelabels.forEach((pl) => {pl.isPrelabel = true;})
        },
        getTokenFromData(dataName, dataValue) {
            return this.tokenizedText.tokens.filter((t) => {
                return t[dataName] === dataValue;
            })[0]
        },
        getTokenFromStart(start) {
            return this.getTokenFromData('start', start);
        },
        getTokenFromEnd(end) {
            return this.getTokenFromData('end', end);
        },
        getNodeFromToken(token) {
            return document.getElementById(this.getTokenId(token.id));
        },
        getTokenFromNode(node) {
            return this.tokenizedText.tokens[this.getTokenIdFromNode(node)];
        },
        getTextFromBoundaries(start, end) {
            return [...this.tokenizedText.text].slice(start, end).join('');
        },
        getTokenIdFromNode(node) {
            return parseInt(node.id.split('_')[1]);
        },
        getTokenId(n) {
            return `tok_${n}`;
        },
        getSelectionId(startId, endId) {
            return `sel_${startId}_${endId}`;
        },
    },
    computed: {
        selectedCategory: function () {
            return config.categories[this.selectedLabel];
        }
    },
    watch: {
        selectedLabel: function (){
            this.updateHighlightingColor(this.getCategoryColor(this.selectedCategory, true));
        },
        tokenizedText: function(){
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
        this.updateHighlightingColor(this.getCategoryColor(this.selectedCategory, true));
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