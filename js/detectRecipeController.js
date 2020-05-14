var app = angular.module('detectionRecipe.detect', []);

app.controller('detectRecipeController', function($scope) {


    var retrieveCanUseGPU = function() {

        $scope.callPythonDo({method: "get-gpu-info"}).then(function(data) {
            $scope.canUseGPU = data["can_use_gpu"];
            $scope.finishedLoading = true;
        }, function(data) {
            $scope.canUseGPU = false;
            $scope.finishedLoading = true;
        });
    };

    var initVariable = function(varName, initValue) {
        if ($scope.config[varName] == undefined) {
            $scope.config[varName] = initValue;
        }
    };

    var initVariables = function() {
        initVariable("batch_size", 1);
        initVariable("confidence", 0.5);
        initVariable("gpu_allocation", 0.5);
        initVariable("list_gpu", "0");
        initVariable("record_missing", false);
    };

    var init = function() {
        $scope.finishedLoading = false;
        initVariables();
        retrieveCanUseGPU();
    };

    init();
});

