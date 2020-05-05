import {APIErrors} from "../dku-api.js";

let ErrorsComponent = {
    data: function () {
        return {errors: APIErrors}
    },
    methods: {
        clearAll: function () {
            APIErrors.length = 0;
            this.$forceUpdate();
        }
    },
    // language=HTML
    template: `
        <div class="errors-background" v-if="errors.length">
            <div class="errors" >
                <div v-on:click="clearAll()" class="errors--close">✖</div>
                <div class="errors-container">
                    <div v-for="e in errors">
                        <div>{{e.statusText}}</div>
                        <p class="error-name">{{e.data.error}}</p>
                        <pre v-if="e.data && e.data.trace">{{e.data.trace}}</pre>
                    </div>
                </div>
            </div>
        </div>`
};
export {ErrorsComponent}
