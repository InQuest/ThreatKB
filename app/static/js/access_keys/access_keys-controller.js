'use strict';

angular.module('ThreatKB')
    .controller('AccessKeysController', ['$scope', 'resolvedAccessKeys', 'AccessKeys',
        function ($scope, resolvedAccessKeys, AccessKeys) {

            $scope.access_keys = resolvedAccessKeys;

            $scope.create = function () {
                AccessKeys.save(function () {
                    $scope.access_keys = AccessKeys.query();
                });
            };

            $scope.update = function (id, status) {
                $scope.access_key = AccessKeys.get({id: id});
                $scope.access_key.status = status ? 'active' : 'inactive';
                AccessKeys.update({id: id}, $scope.access_key,
                    function () {
                        $scope.access_keys = AccessKeys.query();
                    });
            };

            $scope.delete = function (id) {
                $scope.access_key = AccessKeys.get({id: id});
                $scope.access_key.status = 'deleted';
                AccessKeys.update({id: id}, $scope.access_key,
                    function () {
                        $scope.access_keys = AccessKeys.query();
                    });
            };

        }]);
