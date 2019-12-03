let TabularSample = {
    props: ['item'],
    // language=HTML
    template: `
        <div class="tabular-sample">
            <table>
                <tr>
                    <th class="tabular-sample--key tabular-sample--header">Column</th>
                    <th class="tabular-sample--value tabular-sample--header">Value</th>
                </tr>
                <tr v-for="(value, name, index) in item.raw" v-bind:class="{ odd: index%2 }">
                    <td class="tabular-sample--key">{{name}}</td>
                    <td class="tabular-sample--value">{{value}}</td>
                </tr>
            </table>
        </div>`
};

export {TabularSample}
