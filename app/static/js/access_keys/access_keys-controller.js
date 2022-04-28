'use strict';

angular.module('ThreatKB')
    .controller('AccessKeysController', ['$scope', '$http', '$uibModal', 'resolvedAccessKeys', 'AccessKeys', 'growl', 'FileSaver', 'Blob',
        function ($scope, $http, $uibModal, resolvedAccessKeys, AccessKeys, growl, FileSaver, Blob) {

            $scope.access_keys = resolvedAccessKeys;

            $scope.getActiveInactiveCount = function () {
                AccessKeys.getActiveInactiveCount().then(function (response) {
                    $scope.activeInactiveCount = response.data.activeInactiveCount;
                }, function (error) {
                });
            };
            $scope.getActiveInactiveCount();

            $scope.get_cli = function () {
                AccessKeys.get_cli().then(function (response) {
                    var header = response.headers()['content-disposition'];
                    //var startIndex = header.indexOf('filename=');
                    //var filename = header.slice(startIndex + 9);
                    var filename = "threatkb.py";
                    try {
                        FileSaver.saveAs(new Blob([response.data], {type: response.headers()["Content-Type"]}), filename);
                    }
                    catch (error) {
                        growl.error(error.message, {ttl: -1});
                    }
                }, function (error) {
                    growl.error(error.data, {ttl: -1});
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
                    },
                    size: 'lg'
                });

                keyGen.result.then(function (keys) {
                    $scope.access_keys = keys;
                    $scope.refresh();
                });
            };
        }])
    .controller('AccessKeysGeneratedController', ['$scope', '$http', '$uibModalInstance', 'access_keys', 'AccessKeys', 'FileSaver', 'Blob',
        function ($scope, $http, $uibModalInstance, access_keys, AccessKeys, FileSaver, Blob) {
            $scope.access_keys = access_keys;

            $scope.downloadKey = function () {
                var string_csv = "Token," + $scope.access_key.token + "\nSecretKey," + $scope.access_key.s_key;
                FileSaver.saveAs(new Blob([string_csv], {type: "text/csv"}), 'access_key.csv');
            };

            AccessKeys.resource.save(function (response) {
                $scope.access_key = response;

                $scope.key_csv.push("Token=" + $scope.access_key.token);
                $scope.key_csv.push("SecretKey=" + $scope.access_key.s_key);
            });

            $scope.close = function () {
                $uibModalInstance.close($scope.access_keys);
            };
        }]);
