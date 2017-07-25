'use strict';

angular.module('InquestKB')
    .controller('Cfg_statesController', ['$scope', '$modal', 'resolvedCfg_states', 'Cfg_states',
        function ($scope, $modal, resolvedCfg_states, Cfg_states) {

            $scope.cfg_states = resolvedCfg_states;

            $scope.create = function () {
                $scope.clear();
                $scope.open();
            };

            $scope.update = function (id) {
                $scope.cfg_states = Cfg_states.get({id: id});
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
                $scope.cfg_states = {

                    "state": "",

                    "id": ""
                };
            };

            $scope.open = function (id) {
                var cfg_statesSave = $modal.open({
                    templateUrl: 'cfg_states-save.html',
                    controller: 'Cfg_statesSaveController',
                    resolve: {
                        cfg_states: function () {
                            return $scope.cfg_states;
                        }
                    }
                });

                cfg_statesSave.result.then(function (entity) {
                    $scope.cfg_states = entity;
                    $scope.save(id);
                });
            };
        }])
    .controller('Cfg_statesSaveController', ['$scope', '$modalInstance', 'cfg_states',
        function ($scope, $modalInstance, cfg_states) {
            $scope.cfg_states = cfg_states;


            $scope.ok = function () {
                $modalInstance.close($scope.cfg_states);
            };

            $scope.cancel = function () {
                $modalInstance.dismiss('cancel');
            };
        }]);
