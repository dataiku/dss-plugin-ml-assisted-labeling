/*
Helper function to query webapp backend with a default implementation for error handling
*/

function getUrl(path) {
    return dataiku.getWebAppBackendUrl(path);
}

function dkuDisplayError(error) {
    alert('Backend error, check the logs.');
}

function get(path, args = {}, displayErrors = true) {
    return fetch(getUrl(path) + '?' + $.param(args), {
        method: 'GET',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    })
        .then(response => {
            if (response.status == 502) {
                throw Error("Webapp backend not started");
            } else if (!response.ok) {
                throw Error(`${response.statusText} (HTTP ${response.status})`);
            }
            try {
                return response.json();
            } catch {
                throw Error('The backend response is not JSON: ' + response.text());
            }
        })
        .catch(function (error) {
            if (displayErrors && error.message && !error.message.includes('not started')) { // little hack, backend not started should be handled elsewhere
                dkuDisplayError(error);
            }
            throw error;
        });
}

function post(path, data = {}, displayErrors = true) {
    return fetch(getUrl(path), {
        method: 'POST',
        body: JSON.stringify(data),
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    })
        .then(response => {
            if (response.status == 502) {
                throw Error("Webapp backend not started");
            } else if (!response.ok) {
                throw Error(`${response.statusText} (HTTP ${response.status})`);
            }
            try {
                return response.json();
            } catch {
                throw Error('The backend response is not JSON: ' + response.text());
            }
        })
        .catch(function (error) {
            if (displayErrors && error.message && !error.message.includes('not started')) { // little hack, backend not started should be handled elsewhere
                dkuDisplayError(error);
            }
            throw error;
        });
}

const webappBackend = Object.freeze({getUrl, get, post});