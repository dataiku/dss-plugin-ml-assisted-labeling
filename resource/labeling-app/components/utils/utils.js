import {DKUApi} from "../../dku-api.js";

export const UNDEFINED_COLOR = [102, 102, 102];
export const UNDEFINED_CAPTION = 'missing ?';
const EMPTY_KEY = "no_key"  // Must be changed on back as well

function hexToRgb(hex) {
    // Expand shorthand form (e.g. "03F") to full form (e.g. "0033FF")
    const shorthandRegex = /^#?([a-f\d])([a-f\d])([a-f\d])$/i;
    hex = hex.replace(shorthandRegex, function (m, r, g, b) {
        return r + r + g + g + b + b;
    });

    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
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

export let config = undefined;

export function savePerIterationConfig(configResponse) {
    if (config) {
        config.isAlEnabled = configResponse.al_enabled;
        config.haltingThresholds = configResponse.halting_thr;
        config.stoppingMessages = configResponse.stopping_messages;
        config.classifierConfig = configResponse.classifier_config;
    }
}

export function loadConfig() {
    function getColorFromPreparedList(elIdx, totalCount) {
        let preset = null;

        // precooked list of 21 most distinct colors (https://sashat.me/2017/01/11/list-of-20-simple-distinct-colors/) :
        // https://medialab.github.io/iwanthue/
        if (totalCount <= 10) {
            preset = [[178, 45, 45], [242, 162, 0], [246, 216, 88], [201, 204, 153], [81, 163, 154], [0, 190, 204], [112, 51, 204], [215, 57, 101], [255, 0, 13], [102, 77, 90]]
        } else if (totalCount <= 21) {
            preset = [[230, 25, 75], [60, 180, 75], [240, 180, 63], [0, 130, 200], [245, 130, 48], [145, 30, 180], [87, 168, 238], [240, 50, 230], [194, 200, 81], [232, 94, 89], [0, 128, 128], [116, 86, 245], [170, 110, 40], [136, 111, 101], [128, 0, 0], [105, 179, 172], [128, 128, 0], [238, 162, 133], [0, 0, 128], [128, 128, 128]]
        }
        return preset && preset[elIdx]
    }

    let webAppConfig = dataiku.getWebAppConfig();
    const categories = {};

    return DKUApi.config().then(data => {
        let localCategories = data.local_categories || [];
        let allCategories = webAppConfig.categories || [];
        allCategories = allCategories.concat(localCategories);

        if (allCategories) {
            allCategories.forEach((el, idx) => {
                categories[el.from || EMPTY_KEY] = {
                    caption: el.to || el.from,
                    color: getColorFromPreparedList(idx, allCategories.length) || stringToRgb(el.from)
                }
            });
            webAppConfig.categories = categories;
        }
        config = webAppConfig;
        savePerIterationConfig(data)
        return config;
    });
}

export function shortcut(event) {
    const shortcuts = {
        'multi-selection': [event.ctrlKey, event.metaKey, event.shiftKey],
        'delete': [event.key === "Delete", event.key === "Backspace"],
        'back': [event.code === 'ArrowLeft'],
        'next': [event.code === 'ArrowRight', event.code === 'Space'],
        'skip': [event.code === 'Tab']
    }
    return (action) => {
        return shortcuts[action].some(x => x);
    }
}


