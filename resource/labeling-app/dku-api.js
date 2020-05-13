axios.defaults.baseURL = dataiku.getWebAppBackendUrl('');
axios.interceptors.response.use((response) => {
    return response.data;
}, (error) => {
    APIErrors.push(error.response);
    return Promise.reject(error);
});

export let APIErrors = [];

export let DKUApi = {

    batch: () => axios.get('batch'),
    config: () => axios.get('config'),
    back: (labelId) => axios.post('back', {labelId}),
    next: (labelId) => axios.post('next', {labelId}),
    first: () => axios.post('first'),
    skip: (data) => axios.post('skip', data),
    label: data => axios.post('label', data)
};
