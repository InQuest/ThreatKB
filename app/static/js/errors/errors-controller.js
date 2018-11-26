'use strict';

angular.module('ThreatKB')
    .controller('ErrorsController', ['$scope', '$uibModal', 'resolvedErrors', 'Errors',
        function ($scope, $uibModal, resolvedErrors, Errors) {

            $scope.errors = resolvedErrors;

            $scope.customSearch = function(actual, expected) {
                if (expected.length < 3) {
                    return true;
                } else if (typeof actual !== "object") {
                    return actual.toString().toLowerCase().indexOf(expected.toString().toLowerCase()) !== -1;
                } else {
                    return false;
                }
            };

            $scope.create = function () {
                $scope.clear();
                $scope.open();
            };

            $scope.show = function (id) {
                $scope.error = Errors.get({id: id});
                $scope.open(id);
            };

            $scope.clear = function () {
                $scope.error = {
                    "route": "",
                    "remote_addr": "",
                    "args": "",
                    "stacktrace": "",
                    "method": "",
                    "id": ""
                };
            };

            $scope.open = function (id) {
                var ErrorsSave = $uibModal.open({
                    templateUrl: 'errors-show.html',
                    controller: 'ErrorsSaveController',
                    resolve: {
                        error: function () {
                            return $scope.error;
                        }
                    }
                });

                ErrorsSave.result.then(function (entity) {
                    $scope.error = entity;
                    $scope.save(id);
                });
            };
        }])
    .controller('ErrorsSaveController', ['$scope', '$uibModalInstance', 'error',
        function ($scope, $uibModalInstance, error) {
            $scope.error = error;

            $scope.ok = function () {
                $uibModalInstance.close($scope.error);
            };

            $scope.cancel = function () {
                $uibModalInstance.dismiss('cancel');
            };
        }]);
