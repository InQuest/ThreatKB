'use strict';

angular.module('ThreatKB')
    .controller('Cfg_settingsController', ['$scope', '$uibModal', 'resolvedCfg_settings', 'Cfg_settings',
        function ($scope, $uibModal, resolvedCfg_settings, Cfg_settings) {

            $scope.cfg_settings = resolvedCfg_settings;

            $scope.create = function () {
                $scope.clear();
                $scope.open();
            };

            $scope.update = function (key) {
                $scope.cfg_settings = Cfg_settings.get({key: key});
                $scope.open(key);
            };

            $scope.delete = function (key) {
                Cfg_settings.delete({key: key},
                    function () {
                        $scope.cfg_settings = Cfg_settings.query();
                    });
            };

            $scope.save = function (key) {
                if (key) {
                    Cfg_settings.update({key: key}, $scope.cfg_settings,
                        function () {
                            $scope.cfg_settings = Cfg_settings.query();
                            //$scope.clear();
                        });
                } else {
                    Cfg_settings.save($scope.cfg_settings,
                        function () {
                            $scope.cfg_settings = Cfg_settings.query();
                            //$scope.clear();
                        });
                }
            };

            $scope.clear = function () {
                $scope.cfg_settings = {

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
                            return $scope.cfg_settings;
                        }
                    }
                });

                cfg_settingsSave.result.then(function (entity) {
                    $scope.cfg_settings = entity;
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
