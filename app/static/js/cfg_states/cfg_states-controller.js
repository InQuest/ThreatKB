'use strict';

angular.module('ThreatKB')
    .controller('Cfg_statesController', ['$scope', '$uibModal', 'resolvedCfg_states', 'Cfg_states',
        function ($scope, $uibModal, resolvedCfg_states, Cfg_states) {

            $scope.cfg_states = resolvedCfg_states;

            $scope.create = function () {
                $scope.clear();
                $scope.open();
            };

            $scope.update = function (id) {
                $scope.cfg_state = Cfg_states.get({id: id});
                $scope.open(id);
            };

            $scope.delete = function (id) {
                Cfg_states.delete({id: id},
                    function () {
                        $scope.cfg_states = Cfg_states.query();
                    });
            };

            $scope.save = function (id) {
                if (id) {
                    Cfg_states.update({id: id}, $scope.cfg_states,
                        function () {
                            $scope.cfg_states = Cfg_states.query();
                            //$scope.clear();
                        });
                } else {
                    Cfg_states.save($scope.cfg_states,
                        function () {
                            $scope.cfg_states = Cfg_states.query();
                            //$scope.clear();
                        });
                }
            };

            $scope.clear = function () {
                $scope.cfg_state = {

                    "state": "",

                    "id": ""
                };
            };

            $scope.open = function (id) {
                var cfg_statesSave = $uibModal.open({
                    templateUrl: 'cfg_states-save.html',
                    controller: 'Cfg_statesSaveController',
                    resolve: {
                        cfg_states: function () {
                            return $scope.cfg_state;
                        }
                    }
                });

                cfg_statesSave.result.then(function (entity) {
                    $scope.cfg_states = entity;
                    $scope.save(id);
                });
            };
        }])
    .controller('Cfg_statesSaveController', ['$scope', '$uibModalInstance', 'cfg_states',
        function ($scope, $uibModalInstance, cfg_states) {
            $scope.cfg_states = cfg_states;

            $scope.set_as_release_state = function () {
                if ($scope.cfg_states.is_release_state) {
                    $scope.clear_states();
                } else {
                    $scope.cfg_states.is_draft_state = false;
                    $scope.cfg_states.is_release_state = true;
                    $scope.cfg_states.is_retired_state = false;
                }
            };

            $scope.set_as_retired_state = function () {
                if ($scope.cfg_states.is_retired_state) {
                    $scope.clear_states();
                } else {
                    $scope.cfg_states.is_draft_state = false;
                    $scope.cfg_states.is_release_state = false;
                    $scope.cfg_states.is_retired_state = true;
                }
            };

            $scope.clear_states = function () {
                $scope.cfg_states.is_draft_state = false;
                $scope.cfg_states.is_release_state = false;
                $scope.cfg_states.is_retired_state = false;
            }

            $scope.set_as_draft_state = function () {
                if ($scope.cfg_states.is_draft_state) {
                    $scope.clear_states();
                } else {
                    $scope.cfg_states.is_draft_state = true;
                    $scope.cfg_states.is_release_state = false;
                    $scope.cfg_states.is_retired_state = false;
                }
            };

            $scope.ok = function () {
                $uibModalInstance.close($scope.cfg_states);
            };

            $scope.cancel = function () {
                $uibModalInstance.dismiss('cancel');
            };
        }]);
