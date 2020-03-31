export const UNDEFINED_COLOR = [220, 220, 220];

function hexToRgb(hex) {
    // Expand shorthand form (e.g. "03F") to full form (e.g. "0033FF")
    var shorthandRegex = /^#?([a-f\d])([a-f\d])([a-f\d])$/i;
    hex = hex.replace(shorthandRegex, function (m, r, g, b) {
        return r + r + g + g + b + b;
    });

    var result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? [
        parseInt(result[1], 16),
        parseInt(result[2], 16),
        parseInt(result[3], 16)
    ] : null;
}


export function stringToRgb(str) {
    return hexToRgb(stringToColor(str))
}

export function debounce(callback, wait) {
    let timeout;
    return (...args) => {
        const context = this;
        clearTimeout(timeout);
        timeout = setTimeout(() => callback.apply(context, args), wait);
    };
}

export let config = (() => {
    function getColorFromPreparedList(elIdx, totalCount) {
        let preset = null;

        // precooked list of 21 most distinct colors (https://sashat.me/2017/01/11/list-of-20-simple-distinct-colors/) :
        // https://medialab.github.io/iwanthue/
        if (totalCount <= 10) {
            preset = [[178, 45, 45], [242, 162, 0], [238, 255, 0], [201, 204, 153], [0, 255, 136], [0, 190, 204], [112, 51, 204], [214, 182, 242], [255, 0, 136], [102, 77, 90]]
        } else if (totalCount <= 21) {
            preset = [[230, 25, 75], [60, 180, 75], [255, 225, 25], [0, 130, 200], [245, 130, 48], [145, 30, 180], [70, 240, 240], [240, 50, 230], [210, 245, 60], [250, 190, 190], [0, 128, 128], [230, 190, 255], [170, 110, 40], [255, 250, 200], [128, 0, 0], [170, 255, 195], [128, 128, 0], [255, 215, 180], [0, 0, 128], [128, 128, 128], [255, 255, 255]]
        }
        return preset && preset[elIdx]
    }

    let webAppConfig = dataiku.getWebAppConfig();
    const categories = {};
    if (webAppConfig.categories) {
        webAppConfig.categories.forEach((el, idx) => {
            categories[el.from] = {
                caption: el.to || el.from,
                color: getColorFromPreparedList(idx, webAppConfig.categories.length) || stringToRgb(el.from)
            }
        });
        webAppConfig.categories = categories;
    }
    return webAppConfig;
})();

