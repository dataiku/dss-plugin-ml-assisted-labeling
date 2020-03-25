/*global fabric*/

const STROKE_WIDTH = 3;

function modifyFabric() {
    fabric.Group.prototype.hasControls = false
    fabric.Rect.prototype.noScaleCache = false
    fabric.Rect.prototype.hasRotatingPoint = false
    fabric.Object.prototype.objectCaching = false;
    fabric.Rect.prototype.toObject = (function () {
        return function () {
            return {
                id: this.id,
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
        img: String,
        value: Array,
        selectedLabel: String,
        labelConfig: Object
    },
    data() {
        return {
            canvas: null,
            scale: null,
            mode: 'draw',
        }
    },
    methods: {
        toggleMode(mode) {
            this.mode = (this.mode === mode ? 'normal' : mode);
        },
        loadBackground() {
            return new Promise((resolve) => {
                const background = new Image();
                resolve();
                // background.onload = () => {
                // };
                // background.src = this.img;
            });
        },

        uuidv4() {
            return ([1e7] + -1e3 + -4e3 + -8e3 + -1e11).replace(/[018]/g, c =>
                (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
            );
        },
        drawData() {
            this.canvas.remove(...this.canvas.getObjects());
            this.value && this.value.forEach(s => {
                this.addRectFromObject(s)
            });
            this.canvas.renderAll();
        },
        getShapesDataFromCanvas() {
            let canvas = this.canvas;
            return canvas.toJSON(['id', 'selected', 'label']).objects
        },

        addRectFromObject(o) {
            let color = this.labelConfig[o.label].color;
            const colorStr = `rgb(${color[0]},${color[1]},${color[2]}, 0.5)`;
            const strokeColorStr = `rgb(${color[0]},${color[1]},${color[2]}, 0.8)`;
            let rect = new fabric.Rect({
                id: o.id || this.uuidv4(),
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
            let color = this.labelConfig[selectedLabel].color;
            const colorStr = `rgb(${color[0]},${color[1]},${color[2]}, 0.5)`;
            const strokeColorStr = `rgb(${color[0]},${color[1]},${color[2]}, 0.8)`;
            let rect = new fabric.Rect({
                id: id || this.uuidv4(),
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
    watch: {
        value: {
            handler(nv) {
                const canvas = this.canvas;
                if (JSON.stringify(nv) !== JSON.stringify(this.getShapesDataFromCanvas())) { // TODO: maybe use fabric's hasStateChanged
                    this.drawData();

                    canvas.discardActiveObject();
                    let selected = nv.filter(o => o.selected).map(o => o.id);
                    if (selected.length === 1) {
                        canvas.setActiveObject(canvas.getObjects().find(o => o.id === selected[0]));
                    }
                    this.canvas.requestRenderAll();
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
        this.canvas.uniScaleTransform = true;

        const canvas = this.canvas; // shortcut

        let img = fabric.Image.fromURL(this.img, function (img) {
            // Fit image to canvas
            if (img.height * img.scaleY > canvas.height) {
                img.scaleToHeight(canvas.height);
            }
            if (img.width * img.scaleX > canvas.width) {
                img.scaleToWidth(canvas.width);
            }
            // Shrink canvas to image
            canvas.setWidth(img.width * img.scaleX);
            canvas.setHeight(img.height * img.scaleY);

            canvas.setBackgroundImage(img);
            canvas.requestRenderAll();
        });


        let rect, isDrawing, isDown, origX, origY;


        modifyFabric();


        canvas.on('after:render', () => {
            this.$emit("input", canvas.toObject().objects);
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
                    this.$emit("input", canvas.toObject().objects);
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
        window.addEventListener('keydown', (event) => {
            if (event.key === "Shift") {
                this.mode = 'normal';
            }
            if (event.key === 'Control') {
                this.mode = 'draw';
            }
        });

        this.drawData();
    },


    // language=HTML
    template: `
        <div class="canvas-wrapper" ref="wrapper">
            <!--            <code>VALUE: {{value}}</code>-->
            <div>
                <canvas ref="canvas" width="900" height="600"></canvas>
            </div>
            <button @click="toggleMode('draw')" class="tool-selector">
                <span v-if="mode !== 'draw'"><i class="fas fa-pencil-alt"></i>Draw</span>
                <span v-if="mode === 'draw'"><i class="far fa-object-ungroup"></i>Select</span>
            </button>
        </div>`
};

export {ImageCanvas}
