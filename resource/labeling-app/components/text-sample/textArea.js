import {config, UNDEFINED_COLOR, UNDEFINED_CAPTION, shortcut} from "../utils/utils.js";


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
        prelabels: {
            type: Array,
            default: () => {
                return [];
            }
        },
        tokenSep: String,
        textDirection: String,
        tokenizedText: Object
    },
    data() {
        return {
            splitter: null,
        }
    },
    computed: {
        splittedText: function () {
            return this.splitText(this.text, this.tokenSep);
        }
    },
    methods: {
        splitText(txt, tokenSep=' ') {
            const splitted_text = tokenSep === '' ? this.splitter.splitGraphemes(txt) : txt.split(tokenSep)
            return splitted_text.map((x) => this.sanitizeToken(x, tokenSep)).reduce((x, y) => x.concat(y));
        },
        sanitizeToken(token) {
            const sanitizedTokenList = [];
            if (token.match(/^[\p{L}\p{N}]*$/gu)) {
                sanitizedTokenList.push({token});
            } else {
                let currentToken = '';
                this.splitter.splitGraphemes(token).forEach((c) => {
                    if (c.match(/^[\p{L}\p{N}]*$/gu)) {
                        currentToken += c;
                    } else {
                        currentToken && sanitizedTokenList.push({token: currentToken});
                        sanitizedTokenList.push({token: c});
                        currentToken = '';
                    }
                })
                if (currentToken) sanitizedTokenList.push({token: currentToken});
            }
            sanitizedTokenList[sanitizedTokenList.length - 1].sepAtEnd = true;
            return sanitizedTokenList;
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
            const newRange = document.createRange();
            const startNode = document.getElementById(this.getTokenId(e.tokenStart));
            const endNode = document.getElementById(this.getTokenId(e.tokenEnd));
            newRange.setStartBefore(startNode);
            newRange.setEndAfter(endNode);
            this.makeSelected(newRange, category, e.selected, e.isPrelabel)
        },
        getTextFromBoundaries(start, end) {
            return this.text.slice(start, end)
        },
        handleDblClickOnSelection(selectionId) {
            return () => {
                const newEntities = this.entities.filter(
                    (x) => selectionId !== this.getSelectionId(x.tokenStart, x.tokenEnd));
                this.$emit("update:entities", newEntities);
            }
        },
        handleClickOnSelection(selectionId) {
            return (mEvent) => {
                this.mapAndEmit((o) => {
                    if (selectionId === this.getSelectionId(o.tokenStart, o.tokenEnd)) {
                        o.selected = !o.selected;
                    } else {
                        o.selected = shortcut(mEvent)('multi-selection') ? o.selected : false;
                    }
                })
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

            selectionWrapper.addEventListener('dblclick', this.handleDblClickOnSelection(selectionId));
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

            selected && selectionWrapper.scrollIntoView();
        },
        getLabeledText(start, end, tokenStart, tokenEnd) {
            return {
                label: this.selectedLabel,
                text: this.getTextFromBoundaries(start, end),
                start: start,
                end: end,
                tokenStart: tokenStart,
                tokenEnd: tokenEnd,
                draft: false,
                selected: !this.selectedLabel,
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
                const textContent = [...this.tokenizedText.text].slice(token.start, token.end).join('');
                newToken.textContent = textContent + token.whitespace;
                newToken.classList.add('token');
                newToken.id = this.getTokenId(index);
                newToken.setAttribute('data-start', token.start);
                newToken.setAttribute('data-end', token.end);
                textarea.appendChild(newToken)
            })
            // let charCpt = 0;
            // this.splittedText.forEach((token, index) => {
            //     const newToken = document.createElement('span');
            //     newToken.textContent = token.token + (token.sepAtEnd ? this.tokenSep: '');
            //     newToken.classList.add('token');
            //     newToken.id = this.getTokenId(index);
            //     newToken.setAttribute('data-start', charCpt);
            //     newToken.setAttribute('data-end', (charCpt + this.splitter.splitGraphemes(token.token).length).toString());
            //     charCpt += this.splitter.splitGraphemes(newToken.textContent).length;
            //     textarea.appendChild(newToken)
            // })
        },
        handleMouseUp() {
            const selection = document.getSelection();
            if (selection.isCollapsed || selection.toString() === this.tokenSep) return;
            const range = selection.getRangeAt(0);
            let [startNode, endNode] = [range.startContainer, range.endContainer]
            if (range.toString().startsWith(this.tokenSep)) {
                startNode = startNode.parentElement.nextElementSibling.childNodes[0];
            }
            const {tokenIndex: tokenStart, charStart: charStart} = this.parseTokenId(startNode.parentElement);
            const {tokenIndex: tokenEnd, charEnd: charEnd} = this.parseTokenId(endNode.parentElement);
            if (isNaN(charStart) || isNaN(charEnd)) return;
            if (this.isLegitSelect(tokenStart, tokenEnd)) {
                this.addObjectToObjectList(this.getLabeledText(charStart, charEnd, tokenStart, tokenEnd));
            }
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
        isLegitSelect(startId, endId) {
            return !this.entities || !this.entities.some((o) => {
                return _.intersection(_.range(startId, endId + 1), _.range(o.tokenStart, o.tokenEnd + 1)).length > 0;
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
        enrichPrelabels(entities) {
            if (!entities.length) return;
            const sortedEntities = _.sortBy(entities, ['start']);
            let charCpt = 0;
            let entityIndex = 0;
            let tokenIndex = 0;
            let token, entity;
            while(entityIndex < entities.length) {
                token = this.splittedText[tokenIndex];
                entity = sortedEntities[entityIndex];
                if (!entity.tokenStart && entity.start <= charCpt) {
                    entity.tokenStart = tokenIndex;
                }
                if (entity.end <= charCpt + this.splitter.splitGraphemes(token.token).length) {
                    entity.tokenEnd = tokenIndex;
                    entity.isPrelabel = true;
                    entityIndex += 1;
                }
                charCpt += this.splitter.splitGraphemes(token.token).length + (token.sepAtEnd ? this.tokenSep: '').length;
                tokenIndex += 1
            }
        },
        init_text() {
            this.resetSelection();
            this.enrichPrelabels(this.prelabels);
            this.prelabels?.length && this.emitUpdateEntities(this.prelabels);
        }
    },
    watch: {
        selectedLabel: function (){
            const category = config.categories[this.selectedLabel];
            const color = category ? category.color : UNDEFINED_COLOR;
            this.updateHighlightingColor(this.colorToCSS(color, 0.5));
        },
        text: function(nv){
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
        this.splitter = new GraphemeSplitter();
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

        document.getElementsByClassName('sample-container')[0].addEventListener('click', (event) => {
            this.deselectAll();
        }, true);

    },
    // language=HTML
    template: `
        <div class="labeling-window">
            <div v-bind:class="{
            'textarea-wrapper': true,
            'text-right': textDirection === 'rtl',
            'text-left': textDirection === 'ltr'
            }" ref="wrapper" v-on:mouseup="handleMouseUp"
                 v-bind:dir="textDirection">
                <div class="textarea" id="textarea"></div>
            </div>
            <div class="textarea__button-wrapper">
                <button @click="deleteAll()" class="main-area-element delete-all-btn"><i class="icon-trash"></i>&nbsp;Delete all</button>
            </div>
        </div>`
};

export {TextArea}