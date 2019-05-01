'use strict';

angular.module('ThreatKB')
    .controller('MacrosController', ['$scope', '$uibModal', 'resolvedMacros', 'Macros', 'growl', '$rootScope',
        function ($scope, $uibModal, resolvedMacros, Macros, growl, $rootScope) {

            $scope.macros = resolvedMacros;
            $scope.macro = {};

            const dateRegex = new RegExp(/\d{4}-[01]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-5]\d/);

            $scope.customSearch = function (actual, expected) {
                if (expected.length < 3) {
                    return true;
                } else if (dateRegex.test(actual)) {
                    var pd = $rootScope.pretty_date(actual);
                    if (pd !== undefined) {
                        return pd.toLowerCase().indexOf(expected.toString().toLowerCase()) !== -1;
                    } else {
                        return false;
                    }
                } else if (typeof actual !== "object") {
                    return actual.toString().toLowerCase().indexOf(expected.toString().toLowerCase()) !== -1;
                } else {
                    return false;
                }
            };

            $scope.view_options = ["Active Only", "All", "Inactive Only"];
            $scope.view_selected = "Active Only";
            $scope.change_view = function (item, model) {
                $scope.view_selected = item;

                $scope.macros = Macros.resource.query({view: $scope.view_selected});
            };

            $scope.activate = function (tag) {
                Macros.activate(tag).then(function (success) {
                    growl.info("Successfully activated macro " + tag, {ttl: 3000});
                    $scope.macros = Macros.resource.query({view: $scope.view_selected});
                });
            };

            $scope.create = function () {
                $scope.clear();
                $scope.createMacro();
            };

            $scope.update = function (tag) {
                $scope.macro = Macros.resource.get({tag: tag});
                $scope.macros = Macros.resource.query({view: $scope.view_selected});
                $scope.editMacro(tag);
            };

            $scope.delete = function (tag) {
                Macros.resource.delete({tag: tag},
                    function () {
                        $scope.macro = {};
                        $scope.macros = Macros.resource.query({view: $scope.view_selected});
                    }, function() {
                        growl.info("Unable to permanently delete macro " + tag
                            + " as it's still associated with Signature.", {ttl: 3000});
                    });
            };

            $scope.save = function (tag) {
                if (tag) {
                    Macros.resource.update({tag: tag}, $scope.macro,
                        function () {
                            $scope.macros = Macros.resource.query({view: $scope.view_selected});
                        });
                } else {
                    Macros.resource.save($scope.macro,
                        function () {
                            $scope.macros = Macros.resource.query({view: $scope.view_selected});
                        });
                }
            };

            $scope.clear = function () {
                $scope.macro = {
                    "tag": "",
                    "value": ""
                };
            };

            $scope.createMacro = function (tag) {
                const macrosCreate = $uibModal.open({
                    templateUrl: 'macros-create.html',
                    controller: 'MacrosCreateController',
                    resolve: {
                        macro: function () {
                            return $scope.macro;
                        }
                    }
                });

                macrosCreate.result.then(function (entity) {
                    $scope.macro = entity;
                    $scope.save(tag);
                });
            };

            $scope.editMacro = function (tag) {
                const macrosEdit = $uibModal.open({
                    templateUrl: 'macros-edit.html',
                    controller: 'MacrosEditController',
                    resolve: {
                        macro: function () {
                            return $scope.macro;
                        }
                    }
                });

                macrosEdit.result.then(function (entity) {
                    $scope.macro = entity;
                    $scope.save(tag);
                });
            };
        }])
    .controller('MacrosCreateController', ['$scope', '$uibModalInstance', 'macro',
        function ($scope, $uibModalInstance, macro) {
            $scope.macro = macro;

            $scope.ok = function () {
                $uibModalInstance.close($scope.macro);
            };

            $scope.cancel = function () {
                $uibModalInstance.dismiss('cancel');
            };
        }])
    .controller('MacrosEditController', ['$scope', '$uibModalInstance', 'macro',
        function ($scope, $uibModalInstance, macro) {
            $scope.macro = macro;

            $scope.ok = function () {
                $uibModalInstance.close($scope.macro);
            };

            $scope.cancel = function () {
                $uibModalInstance.dismiss('cancel');
            };
        }]);
