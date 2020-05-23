var app = angular.module('mlAssistedLabelingModule', []);


app.directive('querySamplingSettings', function () {
    return {
        link: function (scope, element, attrs) {
            scope.type = attrs['type'];
            scope.templateUrl = scope.$parent.baseTemplateUrl + "query-sampling-settings-template.html";

            const retrieveCanUseGPU = function () {

                scope.callPythonDo({method: "get-gpu-info"}).then(function (data) {
                    scope.canUseGPU = data["can_use_gpu"];
                    scope.finishedLoading = true;
                }, function (data) {
                    scope.canUseGPU = false;
                    scope.finishedLoading = true;
                });
            };

            const initVariable = function (varName, initValue) {
                if (scope.config[varName] === undefined) {
                    scope.config[varName] = initValue;
                }
            };

            const initVariables = function () {
                initVariable("batch_size", 1);
                initVariable("confidence", 0.5);
                initVariable("gpu_allocation", 0.5);
                initVariable("list_gpu", "0");
                initVariable("record_missing", false);
            };

            const init = function () {
                scope.finishedLoading = false;
                initVariables();
                retrieveCanUseGPU();
            };

            init();
        },
        template: '<div ng-include="templateUrl"></div>'
    }
});

app.value()