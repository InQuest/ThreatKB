'use strict';

angular.module('ThreatKB')
    .controller('AccessKeysController', ['$scope', '$http', '$uibModal', 'resolvedAccessKeys', 'AccessKeys',
        function ($scope, $http, $uibModal, resolvedAccessKeys, AccessKeys) {

            $scope.access_keys = resolvedAccessKeys;

            $scope.getActiveInactiveCount = function () {
                AccessKeys.getActiveInactiveCount().then(function (response) {
                    $scope.activeInactiveCount = response.data.activeInactiveCount;
                }, function (error) {
                });
            };
            $scope.getActiveInactiveCount();

            $scope.update = function (id, status) {
                $scope.access_key = AccessKeys.resource.get({id: id});
                $scope.access_key.status = status ? 'active' : 'inactive';
                AccessKeys.resource.update({id: id}, $scope.access_key,
                    function () {
                        $scope.access_keys = AccessKeys.resource.query();
                        $scope.getActiveInactiveCount();
                    });
            };

            $scope.delete = function (id) {
                $scope.access_key = AccessKeys.resource.get({id: id});
                $scope.access_key.status = 'deleted';
                AccessKeys.resource.update({id: id}, $scope.access_key,
                    function () {
                        $scope.access_keys = AccessKeys.resource.query();
                        $scope.getActiveInactiveCount();
                    });
            };

            $scope.refresh = function () {
                $scope.access_keys = AccessKeys.resource.query();
                $scope.getActiveInactiveCount();
            };

            $scope.open = function () {
                var keyGen = $uibModal.open({
                    templateUrl: 'access_keys-generated.html',
                    controller: 'AccessKeysGeneratedController',
                    resolve: {
                        access_keys: function () {
                            return $scope.access_keys;
                        }
                    }
                });

                keyGen.result.then(function (keys) {
                    $scope.access_keys = keys;
                    $scope.refresh();
                });
            };
        }])
    .controller('AccessKeysGeneratedController', ['$scope', '$http', '$uibModalInstance', 'access_keys', 'AccessKeys',
        function ($scope, $http, $uibModalInstance, access_keys, AccessKeys) {
            $scope.access_keys = access_keys;

            $scope.key_csv = [];

            AccessKeys.resource.save(function (response) {
                $scope.access_key = response;

                $scope.key_csv.push("Token=" + $scope.access_key.token);
                $scope.key_csv.push("SecretKey=" + $scope.access_key.s_key);
            });

            $scope.close = function () {
                $uibModalInstance.close($scope.access_keys);
            };
        }]);
