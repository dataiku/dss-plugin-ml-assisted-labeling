axios.defaults.baseURL = dataiku.getWebAppBackendUrl('');
axios.interceptors.response.use(function (response) {
    return response.data;
}, function (error) {
    console.error(error);
    return Promise.reject(error);
});


let DKUApi = {

    sample: () => axios.get('sample'),
    back: (id) => axios.post('back', {'current': id}),
    skip: (id) => axios.post('skip', {id}),
    classify: data => axios.post('classify', data)
};
export {DKUApi}
