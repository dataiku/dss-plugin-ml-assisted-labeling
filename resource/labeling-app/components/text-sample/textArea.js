import {config, UNDEFINED_COLOR, UNDEFINED_CAPTION} from "../utils/utils.js";
import { PUNCTUATION_REGEX } from "./punctuation.js"


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
        tokenSep: String,
        prelabels: {
            type: Array,
            default: () => {
                return [];
            }
        },
    },
    computed: {
        splittedText: function () {
            return this.splitText(this.text, this.tokenSep);
        }
    },
    methods: {
        splitText(txt, tokenSep=' ') {
            return txt.split(tokenSep).map((x) => this.sanitizeToken(x, tokenSep)).reduce((x, y) => x.concat(y));
        },
        sanitizeToken(token) {
            const sanitizedTokenList = [];
            if (!token.match(PUNCTUATION_REGEX)) {
                sanitizedTokenList.push({token});
            } else {
                let currentToken = '';
                token.split('').forEach((c) => {
                    if (!c.match(PUNCTUATION_REGEX)) {
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
            this.makeSelected(e.tokenStart, e.tokenEnd, category, e.selected)
        },
        addSelection(tokenStart, tokenEnd) {
            const category = config.categories[this.selectedLabel];
            this.makeSelected(tokenStart, tokenEnd, category, false)
        },
        getTextFromBoundaries(start, end) {
            return this.text.slice(start, end)
        },
        makeSelected(tokenStart, tokenEnd, category, selected) {
            const tokenIds = this.getSelectedTokensFromBoundaries(tokenStart, tokenEnd);
            const color = category ? category.color : UNDEFINED_COLOR;
            const colorStrTransparent = this.colorToCSS(color, 0.25);
            const colorStrOpaque = this.colorToCSS(color)

            const caption = category ? category.caption : UNDEFINED_CAPTION;

            const selectedTokens = tokenIds.map((x) => document.getElementById(x));
            const selectionWrapper = document.createElement('mark');
            selectionWrapper.classList.add('selection-wrapper');
            selected && selectionWrapper.classList.add('selected');
            const selectionId = this.getSelectionId(tokenStart, tokenEnd);
            selectionWrapper.id = selectionId;
            selectionWrapper.addEventListener('dblclick', () => {
                const newEntities = this.entities.filter(
                    (x) => selectionId !== this.getSelectionId(x.tokenStart, x.tokenEnd));
                this.$emit("update:entities", newEntities);
            });
            selectionWrapper.addEventListener('click', (mEvent) => {
                this.mapAndEmit((o) => {
                    if (selectionId === this.getSelectionId(o.tokenStart, o.tokenEnd)) {
                        o.selected = !o.selected;
                    } else {
                        o.selected = (mEvent.ctrlKey || mEvent.metaKey) ? o.selected : false;
                    }
                })
            });
            selectionWrapper.style.background = colorStrTransparent
            selectedTokens[0].parentNode.insertBefore(selectionWrapper, selectedTokens[0]);
            selectedTokens.forEach((x) => selectionWrapper.appendChild(x));

            const captionSpan = document.createElement('span');
            captionSpan.classList.add('selected-caption');
            captionSpan.textContent = caption;
            captionSpan.style.color = colorStrOpaque
            selectionWrapper.appendChild(captionSpan);

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
                selected: false
            }
        },
        addObjectToObjectList(newObject) {
            this.emitUpdateEntities(this.entities ? this.entities.concat([newObject]) : [newObject]);
        },
        resetSelection() {
            const textarea = document.getElementById('textarea');
            textarea.innerHTML = "";
            let charCpt = 0;
            this.splittedText.forEach((token, index) => {
                const newToken = document.createElement('span');
                newToken.textContent = token.token + (token.sepAtEnd ? this.tokenSep: '');
                newToken.classList.add('token');
                newToken.id = this.getTokenId(index);
                newToken.setAttribute('data-start', charCpt);
                newToken.setAttribute('data-end', (charCpt + token.token.length).toString());
                charCpt += newToken.textContent.length;
                textarea.appendChild(newToken)
            })
        },
        handleMouseUp() {
            const selection = document.getSelection();
            if (selection.isCollapsed) return;
            const { anchorNode, focusNode } = selection;
            let startNode, endNode;
            [startNode, endNode] = _.sortBy([anchorNode, focusNode], [(o) => {
                return this.parseTokenId(o.parentElement).charStart
            }]);
            const {tokenIndex: tokenStart, charStart: charStart} = this.parseTokenId(startNode.parentElement);
            let {tokenIndex: tokenEnd, charEnd: charEnd} = this.parseTokenId(endNode.parentElement);
            if (this.isLegitSelect(tokenStart, tokenEnd)) {
                this.addSelection(tokenStart, tokenEnd);
                this.addObjectToObjectList(this.getLabeledText(charStart, charEnd, tokenStart, tokenEnd));
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
        getSelectedTokensFromBoundaries(startId, endId) {
            return _.range(startId, endId + 1).map(this.getTokenId);
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
            this.prelabels?.length && this.emitUpdateEntities(this.prelabels);
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