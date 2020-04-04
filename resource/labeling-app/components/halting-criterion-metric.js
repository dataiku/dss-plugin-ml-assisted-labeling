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
            <div class="halting-criterion-cell" v-for="t in drawData"
                 :style="{ width: t.width + '%', backgroundColor: t.color }"></div>
            <div class="halting-criterion-cell halting-criterion-overlay"
                 :style="{width: 100-currentValue * 100 + '%', left: currentValue*100 + '%'}"></div>
            <i class="fas fa-map-pin halting-criterion-pointer" :style="{left: currentValue*100 + '%'}"></i>
            <span style="top: 5px">Efficient</span>
            <span style="right: 0; top: 5px">Not efficient</span>
        </div>`
};

export {HaltingCriterionMetric}
