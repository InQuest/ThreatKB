'use strict';

angular.module('ThreatKB')
    .controller('Cfg_settingsController', ['$scope', '$uibModal', 'resolvedCfg_settings', 'Cfg_settings',
        function ($scope, $uibModal, resolvedCfg_settings, Cfg_settings) {

            $scope.cfg_settings = resolvedCfg_settings;
            $scope.cfg_setting = {};

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

            $scope.update = function (key) {
                $scope.cfg_setting = Cfg_settings.get({key: key});
                $scope.cfg_settings = Cfg_settings.query();
                $scope.open(key);
            };

            $scope.delete = function (key) {
                Cfg_settings.delete({key: key},
                    function () {
                        $scope.cfg_setting = {};
                        $scope.cfg_settings = Cfg_settings.query();
                    });
            };

            $scope.save = function (key) {
                if (key) {
                    Cfg_settings.update({key: key}, $scope.cfg_setting,
                        function () {
                            $scope.cfg_settings = Cfg_settings.query();
                        });
                } else {
                    Cfg_settings.save($scope.cfg_setting,
                        function () {
                            $scope.cfg_settings = Cfg_settings.query();
                        });
                }
            };

            $scope.clear = function () {
                $scope.cfg_setting = {
                    "state": "",
                    "key": ""
                };
            };

            $scope.open = function (key) {
                var cfg_settingsSave = $uibModal.open({
                    templateUrl: 'cfg_settings-save.html',
                    controller: 'Cfg_settingsSaveController',
                    resolve: {
                        cfg_settings: function () {
                            return $scope.cfg_setting;
                        }
                    }
                });

                cfg_settingsSave.result.then(function (entity) {
                    $scope.cfg_setting = entity;
                    $scope.save(key);
                });
            };
        }])
    .controller('Cfg_settingsSaveController', ['$scope', '$uibModalInstance', 'cfg_settings',
        function ($scope, $uibModalInstance, cfg_settings) {
            $scope.cfg_settings = cfg_settings;

            $scope.ok = function () {
                $uibModalInstance.close($scope.cfg_settings);
            };

            $scope.cancel = function () {
                $uibModalInstance.dismiss('cancel');
            };
        }]);
