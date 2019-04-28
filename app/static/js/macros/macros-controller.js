'use strict';

angular.module('ThreatKB')
    .controller('MacrosController', ['$scope', '$uibModal', 'resolvedMacros', 'Macros',
        function ($scope, $uibModal, resolvedMacros, Macros) {

            $scope.macros = resolvedMacros;
            $scope.macro = {};

            $scope.customSearch = function (actual, expected) {
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

            $scope.update = function (tag) {
                $scope.macro = Macros.get({tag: tag});
                $scope.macros = Macros.query();
                $scope.open(tag);
            };

            $scope.delete = function (tag) {
                Macros.delete({tag: tag},
                    function () {
                        $scope.macro = {};
                        $scope.macros = Macros.query();
                    });
            };

            $scope.save = function (tag) {
                if (tag) {
                    Macros.update({tag: tag}, $scope.macro,
                        function () {
                            $scope.macros = Macros.query();
                        });
                } else {
                    Macros.save($scope.macro,
                        function () {
                            $scope.macros = Macros.query();
                        });
                }
            };

            $scope.clear = function () {
                $scope.macro = {
                    "tag": "",
                    "value": ""
                };
            };

            $scope.open = function (tag) {
                const macrosSave = $uibModal.open({
                    templateUrl: 'macros-save.html',
                    controller: 'MacrosSaveController',
                    resolve: {
                        macro: function () {
                            return $scope.macro;
                        }
                    }
                });

                macrosSave.result.then(function (entity) {
                    $scope.macro = entity;
                    $scope.save(tag);
                });
            };
        }])
    .controller('MacrosSaveController', ['$scope', '$uibModalInstance', 'macro',
        function ($scope, $uibModalInstance, macro) {
            $scope.macro = macro;

            $scope.ok = function () {
                $uibModalInstance.close($scope.macro);
            };

            $scope.cancel = function () {
                $uibModalInstance.dismiss('cancel');
            };
        }]);
