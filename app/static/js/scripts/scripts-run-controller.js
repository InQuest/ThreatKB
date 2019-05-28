'use strict';

angular.module('ThreatKB')
    .controller('ScriptsRunController', ['$scope', '$uibModal', 'resolvedScripts', 'growl', 'Script',
        function ($scope, $uibModal, resolvedScripts, growl, Script) {

            $scope.scripts = resolvedScripts;

            $scope.customSearch = function(actual, expected) {
                if (expected.length < 3) {
                    return true;
                } else if (typeof actual !== "object") {
                    return actual.toString().toLowerCase().indexOf(expected.toString().toLowerCase()) !== -1;
                } else {
                    return false;
                }
            };

            $scope.run_script = function (id) {
                $scope.script = Script.resource.get({id: id});
                $scope.open(id);
            };

            $scope.open = function (id) {
                var scriptSave = $uibModal.open({
                    templateUrl: 'script_run_run.html',
                    controller: 'ScriptRunRunController',
                    size: 'lg',
                    backdrop: 'static',
                    resolve: {
                        script: function () {
                            return $scope.script;
                        }
                    }
                });

                scriptSave.result.then(function (entity) {
                    $scope.script = entity;
                    $scope.save(id);
                });
            };

        }])
    .controller('ScriptRunRunController', ['$scope', '$http', '$uibModalInstance', 'script', 'growl', 'Script',
        function ($scope, $http, $uibModalInstance, script, growl, Script) {
            $scope.script = script;

            $scope.onCmLoad = function (_cm) {
                $scope.modeChanged = function () {
                    _cm.setOption("mode", $scope.script.interpreter.toLowerCase());
                    _cm.focus();
                    _cm.autofocus = true;
                };
            };

            $scope.run_script = function () {
                Script.run_script($scope.script.id, $scope.script.arguments_, $scope.script.client_match_regex).then(function (response) {
                        $scope.results = response;
                    },
                    function (error) {
                        growl.error(error.data, {ttl: -1});
                    }
                );
                return false;
            };

            $scope.ok = function () {
                $uibModalInstance.close($scope.script);
            };

            $scope.cancel = function () {
                $uibModalInstance.dismiss('cancel');
            };
        }]);
