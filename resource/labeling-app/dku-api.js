axios.defaults.baseURL = dataiku.getWebAppBackendUrl('');
axios.interceptors.response.use(function (response) {
    return response.data;
}, function (error) {
    console.error(error);
    return Promise.reject(error);
});


let DKUApi = {

    batch: () => axios.get('batch'),
    back: (id) => axios.post('back', {id}),
    skip: (data) => axios.post('skip', data),
    label: data => axios.post('label', data)
};
export {DKUApi}
