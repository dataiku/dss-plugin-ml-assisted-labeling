let HaltingCriterionMetric = {
    props: ['thresholds', 'colors', 'currentValue'],
    data: () => {
        return {
            drawData: null,
        }
    },
    watch: {
        currentValue: function (nv) {
            this.init();
        }
    },
    methods: {
        init() {
            this.drawData = [];
            let cumSum = 0;
            let intervals = this.thresholds.concat(1).sort();
            intervals.forEach((t, idx) => {
                let currWidth = t * 100;
                this.drawData.push({width: currWidth - cumSum, color: this.colors[idx]});
                cumSum += currWidth - cumSum;
            });
            let currentColor = null;
            for (let i = 0; i < intervals.length; i++) {
                currentColor = this.colors[i];
                if (this.currentValue <= intervals[i] && currentColor) {
                    break;
                }
            }
            this.$emit('currentColor', currentColor);
        }
    },
    mounted:function(){
        this.init();
    },
    // language=HTML
    template: `

        <div class="halting-criterion">
            <v-popover :trigger="'hover'">
                <div style="display: flex">
                    <div class="halting-criterion-cell" v-for="t in drawData"
                         :style="{ width: t.width + '%', backgroundColor: t.color }"></div>

                    <div class="halting-criterion-cell halting-criterion-overlay"
                         :style="{width: 100-currentValue * 100 + '%', left: currentValue*100 + '%'}"></div>
                    <i class="fas fa-map-pin halting-criterion-pointer" :style="{left: currentValue*100 + '%'}"></i>
                    <span style="top: 0">Efficient</span>
                    <span style="right: 0; top: 0">Not efficient</span>
                </div>

                <div slot="popover" class="al-status-popover">
                    <div>
                        <p>This bar represents a halting criterion metric.</p>
                        <p>It shows how efficient the labeling process is with Active Learning compared to random sampling.</p>
                        <p>Being in the red zone means that your model should be retrained and labeling should continue after a queries dataset is regenerated.</p>
                    </div>
                </div>
            </v-popover>
        </div>`
};

export {HaltingCriterionMetric}
