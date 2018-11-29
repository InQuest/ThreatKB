'use strict';

angular.module('ThreatKB')
    .controller('ScriptsController', ['$scope', '$uibModal', 'resolvedScripts', 'Script', 'growl',
        function ($scope, $uibModal, resolvedScripts, Script, growl) {

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

            $scope.create = function () {
                $scope.clear();
                $scope.open();
            };

            $scope.update = function (id) {
                $scope.script = Script.resource.get({id: id});
                $scope.open(id);
            };

            $scope.delete = function (id) {
                Script.resource.delete({id: id}, function () {
                    $scope.scripts = Script.resource.query();
                });
            };

            $scope.save = function (id_or_ip) {
                var id = id_or_ip;
                if (typeof(id_or_ip) === "object") {
                    id = id_or_ip.id;
                    $scope.script = id_or_ip;
                }

                if (id) {
                    Script.resource.update({id: id}, $scope.script, function () {
                        $scope.scripts = Script.resource.query();
                        //$scope.clear();
                    });
                } else {
                    Script.resource.save($scope.script, function () {
                        $scope.scripts = Script.resource.query();
                        //$scope.clear();
                    }, function (error) {
                        growl.error(error.data, {ttl: -1});
                    });
                }
            };

            $scope.clear = function () {
                $scope.script = {
                    name: "",
                    description: "",
                    interpreter: "",
                    code: "",
                    match_regex: "",
                    id: ""
                };
            };

            $scope.open = function (id) {
                var scriptSave = $uibModal.open({
                    templateUrl: 'script-save.html',
                    controller: 'ScriptSaveController',
                    size: 'lg',
                    backdrop: 'static',
                    resolve: {
                        script: function () {
                            return $scope.script;
                        }
                    }
                });

                scriptSave.result.then(function (entity) {
                    if (!id) {
                        $scope.save(entity);
                    } else {
                        $scope.script = entity;
                        $scope.save(id);
                    }
                });
            };

        }])
    .controller('ScriptSaveController', ['$scope', '$http', '$uibModalInstance', 'script',
        function ($scope, $http, $uibModalInstance, script) {
            $scope.script = script;

            $scope.interpreters = [
                "python", "erl", "ruby", "sh"
            ];

            if (!$scope.interpreter) {
                $scope.script.interpreter = $scope.interpreters[0];
            }

            if (!script.code) {
                script.code = "Enter code here";
            }

            // The ui-codemirror option
            $scope.cmOption = {
                lineNumbers: true,
                lineWrapping: true,
                indentWithTabs: true,
                autofocus: true,
                onLoad: function (_cm) {
                    $scope.modeChanged = function () {
                        _cm.setOption("mode", $scope.script.interpreter.toLowerCase());
                        _cm.focus();
                        _cm.autofocus = true;
                    };
                }
            };

            $scope.change = function (interpreter) {
                $scope.script.interpreter = interpreter;
            };

            $scope.ok = function () {
                $uibModalInstance.close($scope.script);
            };

            $scope.cancel = function () {
                $uibModalInstance.dismiss('cancel');
            };
        }]);
