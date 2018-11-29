'use strict';

angular.module('ThreatKB')
    .controller('ReleaseController', ['$scope', '$uibModal', 'resolvedRelease', 'Release', 'growl', 'FileSaver', 'Blob', 'blockUI',
        function ($scope, $uibModal, resolvedRelease, Release, growl, FileSaver, Blob, blockUI) {

            $scope.releases = resolvedRelease;

            $scope.block_message = "Generating release. This could take up to a minute...";

            $scope.customSearch = function(input) {
                return typeof input === 'object' ? false : angular.equals(input.toLowerCase(),$scope.searchText.toLowerCase());
            };

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
                    Release.resource.update({id: id}, $scope.release, function (response) {
                        $scope.releases = Release.resource.query();
                    });
                } else {
                    blockUI.start($scope.block_message);
                    Release.resource.save($scope.release, function (response) {
                        $scope.releases = Release.resource.query();
                        growl.info("Successfully built release in " + response.build_time_seconds + " seconds.", {ttl: 3000});
                        blockUI.stop();
                    }, function (error) {
                        blockUI.stop();
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

            $scope.generate_artifact_export = function (id) {
                blockUI.start($scope.block_message);
                Release.generate_artifact_export(id).then(function (response) {
                    var header = response.headers()['content-disposition'];
                    var startIndex = header.indexOf('filename=');
                    var filename = header.slice(startIndex + 9);
                    blockUI.stop();

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
    .controller('ReleaseSaveController', ['$scope', '$http', '$uibModalInstance', 'Release', 'blockUI',
        function ($scope, $http, $uibModalInstance, Release, blockUI) {

            $scope.ok = function () {
                $uibModalInstance.close($scope.release);
            };

            $scope.cancel = function () {
                $uibModalInstance.dismiss('cancel');
            };

        }]);
