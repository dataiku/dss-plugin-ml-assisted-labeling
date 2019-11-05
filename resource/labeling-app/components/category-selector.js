import {DKUApi} from "../dku-api.js";

let CategorySelector = {
    props:['categories','annotation'],
    data: () => ({
        ready: true,
    }),
    methods: {
        shortcutPressed: function (key) {
            if (key <= this.categories.length) {
                if (key === 0 && this.categories.length === 10) {
                    this.classify(this.categories[10].from)
                } else {
                    this.classify(this.categories[key - 1].from)
                }
            }
        },
        classify: function (c) {
            if (this.ready) {
                this.ready = false;

                this.annotation.id = this.$root.sample.id;
                this.annotation.class = c;
                DKUApi.classify(this.annotation).then(sample => {
                    this.ready = true;
                    this.$root.sample = sample;
                })

            }
        }
    },
    // language=HTML
    template: `<div class="category-selector" v-bind:class="{ inactive: !ready }" v-if="annotation">
    <div class="category-selector--categories">
        <div class="button" v-for="(cat, i) in categories"
             v-on:click="classify(cat.from)"
             v-bind:class="{ selected: annotation.class === cat.from }"

        >
            <span>{{cat.to || cat.from}}</span>
            <div class="keybind">{{i+1}}</div>
        </div>
    </div>
    <textarea name="" id="" cols="60" rows="3" placeholder="Comments..." :disabled="!ready"
              v-model="annotation.comment"></textarea>
</div>`,
    mounted: function () {
        window.addEventListener("keydown", (event) => {
            if (event.code.startsWith("Digit")) {
                this.shortcutPressed(parseInt(event.key));
            }
        }, true);
    },
    // language=CSS
};
export {CategorySelector}
