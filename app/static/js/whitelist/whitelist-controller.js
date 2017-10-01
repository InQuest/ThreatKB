'use strict';

angular.module('ThreatKB')
    .controller('WhitelistController', ['$scope', '$uibModal', 'resolvedWhitelist', 'Whitelist',
        function ($scope, $uibModal, resolvedWhitelist, Whitelist) {

            $scope.whitelist = resolvedWhitelist;

            $scope.create = function () {
                $scope.clear();
                $scope.open();
            };

            $scope.update = function (id) {
                $scope.whitelist = Whitelist.get({id: id});
                $scope.open(id);
            };

            $scope.delete = function (id) {
                Whitelist.delete({id: id}, function () {
                    $scope.whitelist = Whitelist.query();
                });
            };

            $scope.save = function (id) {
                if (id) {
                    Whitelist.update({id: id}, $scope.whitelist,
                        function () {
                            $scope.whitelist = Whitelist.query();
                        });
                } else {
                    Whitelist.save($scope.whitelist,
                        function () {
                            $scope.whitelist = Whitelist.query();
                        });
                }
            };

            $scope.clear = function () {
                $scope.whitelist = {
                    whitelist_artifact: "",
                    notes: "",
                    created_time: "",
                    modified_time: "",
                    id: ""

                };
            };

            $scope.open = function (id) {
                var whitelistSave = $uibModal.open({
                    templateUrl: 'white.ist-save.html',
                    controller: 'WhitelistSaveController',
                    resolve: {
                        whitelist: function () {
                            return $scope.whitelist;
                        }
                    }
                });

                whitelistSave.result.then(function (entity) {
                    $scope.whitelist = entity;
                    $scope.save(id);
                });
            };
        }])
    .controller('WhitelistSaveController', ['$scope', '$uibModalInstance', 'whitelist',
        function ($scope, $uibModalInstance, whitelist) {
            $scope.whitelist = whitelist;

            $scope.ok = function () {
                $uibModalInstance.close($scope.whitelist);
            };

            $scope.cancel = function () {
                $uibModalInstance.dismiss('cancel');
            };
        }]);
