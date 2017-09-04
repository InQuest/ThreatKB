'use strict';

angular.module('ThreatKB')
    .controller('ReleaseController', ['$scope', '$uibModal', 'resolvedRelease', 'Release', 'growl', 'FileSaver', 'Blob',
        function ($scope, $uibModal, resolvedRelease, Release, growl, FileSaver, Blob) {

            $scope.releases = resolvedRelease;

            $scope.create = function () {
                $scope.clear();
                $scope.open();
            };

            $scope.delete = function (id) {
                Release.resource.delete({id: id}, function () {
                    $scope.releases = Release.resource.query();
                });
            };

            $scope.save = function (id) {
                if (id) {
                    Release.resource.update({id: id}, $scope.release, function () {
                        $scope.releases = Release.resource.query();
                    });
                } else {
                    Release.resource.save($scope.release, function () {
                        $scope.releases = Release.resource.query();
                    }, function (error) {
                        growl.error(error.data, {ttl: -1});
                    });
                }
            };

            $scope.clear = function () {
                $scope.release = {
                    name: "",
                    is_test_release: "",
                    user: {},
                    date_created: ""
                }
            };

            $scope.open = function (id) {
                var releaseSave = $uibModal.open({
                    templateUrl: 'release-save.html',
                    controller: 'ReleaseSaveController',
                    resolve: {
                        release: function () {
                            return $scope.release;
                        }
                    }
                });

                releaseSave.result.then(function (entity) {
                    $scope.release = entity;
                    $scope.save(id);
                });
            };

            $scope.generate_release_notes = function (id) {
                Release.generate_release_notes(id).then(function (response) {
                    var header = response.headers()['content-disposition'];
                    var startIndex = header.indexOf('filename=');
                    var filename = header.slice(startIndex + 9);
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

            $scope.generate_signature_export = function (id) {
                Release.generate_signature_export(id).then(function (response) {
                    var header = response.headers()['content-disposition'];
                    var startIndex = header.indexOf('filename=');
                    var filename = header.slice(startIndex + 9);
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
        }
    ])
    .controller('ReleaseSaveController', ['$scope', '$http', '$uibModalInstance', 'Release',
        function ($scope, $http, $uibModalInstance, Release) {

            $scope.ok = function () {
                $uibModalInstance.close($scope.release);
            };

            $scope.cancel = function () {
                $uibModalInstance.dismiss('cancel');
            };

        }]);
