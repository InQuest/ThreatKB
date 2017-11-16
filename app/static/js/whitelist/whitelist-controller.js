'use strict';

angular.module('ThreatKB')
    .controller('WhitelistController', ['$scope', '$uibModal', 'resolvedWhitelists', 'Whitelist',
        function ($scope, $uibModal, resolvedWhitelists, Whitelist) {
            $scope.whitelists = resolvedWhitelists;
            $scope.whitelist = {};

            $scope.create = function () {
                $scope.clear();
                $scope.open();
            };

            $scope.update = function (id) {
                $scope.whitelist = Whitelist.get({id: id});
                $scope.whitelists = Whitelist.query();
                $scope.open(id);
            };

            $scope.delete = function (id) {
                Whitelist.delete({id: id}, function () {
                    $scope.whitelist = {};
                    $scope.whitelists = Whitelist.query();
                });
            };

            $scope.save = function (id) {
                if (id) {
                    Whitelist.update({id: id}, $scope.whitelist,
                        function () {
                            $scope.whitelists = Whitelist.query();
                        });
                } else {
                    Whitelist.save($scope.whitelist,
                        function () {
                            $scope.whitelists = Whitelist.query();
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
                    templateUrl: 'whitelist-save.html',
                    controller: 'WhitelistSaveController',
                    resolve: {
                        whitelist: function () {
                            return $scope.whitelist;
                        }
                    }
                });

                whitelistSave.result.then(function (whitelist) {
                    $scope.whitelist = whitelist;
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
