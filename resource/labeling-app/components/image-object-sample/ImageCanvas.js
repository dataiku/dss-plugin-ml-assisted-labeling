/*global fabric*/

import {config, UNDEFINED_COLOR} from "../utils/utils.js";

const STROKE_WIDTH = 3;

function modifyFabric() {
    fabric.Group.prototype.hasControls = false
    fabric.Rect.prototype.noScaleCache = false
    fabric.Rect.prototype.hasRotatingPoint = false
    fabric.Object.prototype.objectCaching = false;
    fabric.Rect.prototype.toObject = (function () {
        return function () {
            return {
                label: this.label,
                left: Math.round(this.left),
                top: Math.round(this.top),
                width: Math.round(this.width * this.scaleX),
                height: Math.round(this.height * this.scaleY),
                selected: this.selected,
                draft: this.draft,

            }
        };
    })(fabric.Rect.prototype.toObject);
}

let ImageCanvas = {

    name: 'ImageCanvas',
    props: {
        base64source: String,
        objects: {
            type: Array,
            default: () => {
                return [];
            }
        },
        selectedLabel: String,
    },
    data() {
        return {
            canvas: null,
            scale: null,
            mode: 'draw',
        }
    },
    methods: {
        deleteAll() {
            canvas.discardActiveObject();
            canvas.remove(...this.canvas.getObjects());
        },
        fillCanvas() {
            this.initialRender = true;

            fabric.Image.fromURL(this.img, (img) => {
                const canvas = this.canvas;
                this.deleteAll();
                canvas.setWidth(this.initialCanvasWidth);
                canvas.setHeight(this.initialCanvasHeight);

                // Fit image to canvas
                if (img.height * img.scaleY > canvas.height) {
                    img.scaleToHeight(canvas.height);
                }
                if (img.width * img.scaleX > canvas.width) {
                    img.scaleToWidth(canvas.width);
                }
                this.backgroundImage = img;

                // Shrink canvas to image
                canvas.setWidth(img.width * img.scaleX);
                canvas.setHeight(img.height * img.scaleY);

                canvas.setBackgroundImage(img);

                if (this.objects) {
                    this.drawData(this.objects.map(this.convertObjectToCanvas));
                }
                canvas.renderAll();
                this.initialRender = false;

            });
        },
        getObjectsWithRealCoords() {
            if (!this.canvas || !this.backgroundImage) {
                return null;
            }
            return this.canvas.toObject().objects.map(o => {
                return {
                    ...o, ...{
                        left: Math.round(o.left / this.backgroundImage.scaleX),
                        top: Math.round(o.top / this.backgroundImage.scaleY),
                        width: Math.round(o.width / this.backgroundImage.scaleX),
                        height: Math.round(o.height / this.backgroundImage.scaleY)
                    }
                };
            });
        },
        toggleMode(mode) {
            this.mode = (this.mode === mode ? 'normal' : mode);
        },
        convertObjectToCanvas(o) {
            return {
                ...o,
                ...{
                    left: Math.round(o.left * this.backgroundImage.scaleX),
                    top: Math.round(o.top * this.backgroundImage.scaleY),
                    width: Math.round(o.width * this.backgroundImage.scaleX),
                    height: Math.round(o.height * this.backgroundImage.scaleY),
                }
            }
        },
        drawData(objects) {
            let objectsToDraw = objects || this.objects;
            let canvas = this.canvas;

            canvas.remove(...canvas.getObjects());
            canvas.discardActiveObject();
            objectsToDraw && objectsToDraw.forEach(s => {
                this.addRectFromObject(s)
            });
            let selectedObjects = canvas.getObjects().filter(o => o.selected);
            selectedObjects.length && canvas.setActiveObject(...selectedObjects);
            canvas.requestRenderAll();
        },
        addRectFromObject(o) {
            let category = config.categories[o.label];
            let color = category ? category.color : UNDEFINED_COLOR;
            const colorStr = `rgb(${color[0]},${color[1]},${color[2]}, 0.5)`;
            const strokeColorStr = `rgb(${color[0]},${color[1]},${color[2]}, 0.8)`;
            let rect = new fabric.Rect({
                left: o.left,
                top: o.top,
                originX: 'left',
                originY: 'top',
                width: o.width,
                height: o.height,
                strokeWidth: STROKE_WIDTH,
                paintFirst: "stroke",
                strokeUniform: true,
                angle: 0,
                fill: colorStr,
                cornerSize: 6,
                stroke: strokeColorStr,
                transparentCorners: false,
                label: o.label,
                selected: o.selected
            });
            this.canvas.add(rect);
            return rect;
        },


        addRect(left, top, width, height, selectedLabel, id) {
            let color = config.categories[selectedLabel].color;
            const colorStr = `rgb(${color[0]},${color[1]},${color[2]}, 0.5)`;
            const strokeColorStr = `rgb(${color[0]},${color[1]},${color[2]}, 0.8)`;
            let rect = new fabric.Rect({
                left: left,
                top: top,
                originX: 'left',
                originY: 'top',
                width: width,
                height: height,
                strokeWidth: STROKE_WIDTH,
                paintFirst: "stroke",
                strokeUniform: true,
                angle: 0,
                fill: colorStr,
                cornerSize: 6,
                stroke: strokeColorStr,
                transparentCorners: false,
                label: selectedLabel,
                draft: false
            });
            this.canvas.add(rect);
            return rect;
        }
    },
    computed: {
        img: function () {
            return 'data:image/png;base64, ' + this.base64source;
        }
    },
    watch: {
        img: function (nv) {
            this.canvas.remove(...this.canvas.getObjects());
            this.fillCanvas();
        },
        objects: {
            handler(nv) {
                if (!nv) {
                    return;
                }
                let objectsWithCanvasCoords = nv.map(this.convertObjectToCanvas);
                if (!this.initialRender && !_.isEqual(objectsWithCanvasCoords, this.canvas.toObject().objects)) { // TODO: maybe use fabric's hasStateChanged
                    this.drawData(objectsWithCanvasCoords);
                }
            },
            deep: true
        },
        mode: {
            immediate: true,
            handler(nv) {
                setTimeout(() => {
                    this.canvas.selection = nv === 'normal';
                    this.canvas.defaultCursor = nv === 'draw' ? 'crosshair' : 'default';
                })
            }
        }
    },
    mounted() {
        this.canvas = new fabric.Canvas(this.$refs.canvas);
        window.canvas = this.canvas;
        this.initialCanvasWidth = this.canvas.width;
        this.initialCanvasHeight = this.canvas.height;
        this.canvas.uniScaleTransform = true;

        const canvas = this.canvas;

        this.fillCanvas();

        let rect, isDrawing, isDown, origX, origY;


        modifyFabric();


        canvas.on('after:render', () => {
            if (this.backgroundImage && !this.initialRender) {
                this.$emit("update:objects", this.getObjectsWithRealCoords());
            }
        });

        canvas.on('mouse:down', (o) => {
            if (this.mode !== 'draw' || !this.selectedLabel) {
                return;
            }
            isDown = true;
            isDrawing = o.target === null;
            if (isDrawing) {
                let pointer = canvas.getPointer(o.e);
                origX = pointer.x;
                origY = pointer.y;
            }
        });

        canvas.on('object:moving', (e) => {
            let target = e.target
                , boundingRect = target.getBoundingRect()
                , height = boundingRect.height
                , width = boundingRect.width
                , top = target.top
                , left = target.left
                , rightBound = this.canvas.width
                , bottomBound = this.canvas.height
                , modified = false;

            if (top < 0) {
                top = 0;
                modified = true;
            }
            if (top + height > bottomBound) {
                top = bottomBound - height;
                modified = true;
            }
            if (left < 0) {
                left = 0;
                modified = true;
            }
            if (left + width > rightBound) {
                left = rightBound - width;
                modified = true;
            }

            if (modified) {
                target.set({left: left});
                target.set({top: top});
                target.setCoords();
            }
        });

        canvas.on('object:scaling', (e) => {
            let obj = e.target;
            obj.setCoords();
            let boundingRect = obj.getBoundingRect(true);

            if (boundingRect.left < 0
                || boundingRect.top < 0
                || boundingRect.left + boundingRect.width > canvas.getWidth()
                || boundingRect.top + boundingRect.height > canvas.getHeight()) {
                obj.top = obj._stateProperties.top;
                obj.left = obj._stateProperties.left;
                obj.angle = obj._stateProperties.angle;
                obj.scaleX = obj._stateProperties.scaleX;
                obj.scaleY = obj._stateProperties.scaleY;
            }
            obj.saveState();
        });

        canvas.on('mouse:move', (o) => {
            if (!isDown) return;
            let pointer = canvas.getPointer(o.e);
            if (isDrawing) {

                let pointerX = Math.max(Math.min(canvas.width - STROKE_WIDTH, pointer.x), 0);
                let pointerY = Math.max(Math.min(canvas.height - STROKE_WIDTH, pointer.y), 0);
                if (!rect) {
                    let width = pointerX - origX;
                    let height = pointerY - origY;
                    rect = this.addRect(origX, origY, width, height, this.selectedLabel);
                    rect.draft = true;
                }

                let currX = Math.max(pointerX, 0);
                let currY = Math.max(pointerY, 0);

                if (origX > currX) {
                    rect.set({left: Math.abs(currX)});
                }
                if (origY > currY) {
                    rect.set({top: Math.abs(currY)});
                }

                rect.set({width: Math.abs(origX - currX)});
                rect.set({height: Math.abs(origY - currY)});
                canvas.requestRenderAll();
            }
        });

        this.canvas.on('mouse:up', () => {
            isDown = false;
            if (this.mode === 'draw') {
                this.canvas.forEachObject(function (o) {
                    o.set({selectable: true}).setCoords();
                });
                if (rect) {
                    rect.draft = false;
                    this.$emit("update:objects", this.getObjectsWithRealCoords());
                    rect = null;
                }
            }
            isDrawing = false;
        });

        canvas.on('selection:cleared', (o) => {
            o.deselected && o.deselected.forEach(o => {
                o.selected = false;
            });
        });
        canvas.on('selection:updated', (o) => {
            o.selected && o.selected.forEach(o => {
                o.selected = true;
            });
            o.deselected && o.deselected.forEach(o => {
                o.selected = false;
            });
        });
        canvas.on('selection:created', (o) => {
            o.selected && o.selected.forEach(o => {
                o.selected = true;
            })
        });

        window.addEventListener('keyup', (event) => {
            if (event.key === "Delete" || event.key === "Backspace") {
                let selection = this.canvas.getActiveObject();

                if (selection.type === 'activeSelection') {
                    selection.forEachObject(o => {
                        this.canvas.remove(o);
                    });
                } else {
                    this.canvas.remove(selection);
                }
                this.canvas.discardActiveObject();
            }
        });
    },


    // language=HTML
    template: `
        <div class="canvas-wrapper" ref="wrapper">
            <div>
                <canvas ref="canvas" width="900" height="600"></canvas>
            </div>
            <div class="canvas__button-wrapper">
                <button @click="toggleMode('draw')">
                    <span v-if="mode !== 'draw'"><i class="fas fa-pencil-alt"></i>Draw</span>
                    <span v-if="mode === 'draw'"><i class="far fa-object-ungroup"></i>Select</span>
                </button>
                <button @click="deleteAll()"><i class="icon-trash"></i>Delete all</button>
            </div>
        </div>`
};

export {ImageCanvas}
