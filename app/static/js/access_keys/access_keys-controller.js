'use strict';

angular.module('ThreatKB')
    .controller('AccessKeysController', ['$scope', '$http', 'resolvedAccessKeys', 'AccessKeys',
        function ($scope, $http, resolvedAccessKeys, AccessKeys) {

            $scope.access_keys = resolvedAccessKeys;

            $scope.getActiveInactiveCount = function () {
                AccessKeys.getActiveInactiveCount().then(function (response) {
                    $scope.activeInactiveCount = response.data.activeInactiveCount;
                }, function (error) {
                });
            };
            $scope.getActiveInactiveCount();

            $scope.create = function () {
                AccessKeys.resource.save(function () {
                    $scope.access_keys = AccessKeys.resource.query();
                    $scope.getActiveInactiveCount();
                });
            };

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

        }]);
