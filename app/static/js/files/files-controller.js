'use strict';

angular.module('ThreatKB')
    .controller('FilesController', ['$scope', '$uibModal', 'resolvedFiles', 'Files', 'Upload', 'growl',
        function ($scope, $uibModal, resolvedFiles, Files, Upload, growl) {

            $scope.files = resolvedFiles;

            $scope.customSearch = function(actual, expected) {
                if (expected.length < 3) {
                    return true;
                } else if (typeof actual !== "object") {
                    return actual.toString().toLowerCase().indexOf(expected.toString().toLowerCase()) !== -1;
                } else {
                    return false;
                }
            };

            $scope.delete = function (id) {
                Files.resource.delete({id: id}, function () {
                    $scope.files = Files.resource.query();
                });
            };

            $scope.refresh = function () {
                $scope.files = Files.resource.query();
            };

            $scope.$watch('files', function () {
                $scope.upload($scope.files);
            });

            $scope.upload = function (id, files) {
                if (files && files.length) {
                    for (var i = 0; i < files.length; i++) {
                        var file = files[i];
                        if (!file.$error) {
                            Upload.upload({
                                url: '/ThreatKB/file_upload',
                                method: 'POST',
                                data: {
                                    file: file
                                }
                            }).then(function (resp) {
                                growl.info('Success ' + resp.config.data.file.name + ' uploaded.', {ttl: 3000});
                                $scope.refresh();
                            }, function (resp) {
                                growl.error(resp.data, {ttl: -1});
                            }, function (evt) {
                                var progressPercentage = parseInt(100.0 * evt.loaded / evt.total);
                                console.log('progress: ' + progressPercentage + '% ' + evt.config.data.file.name);
                            });
                        }
                    }
                }
            };
        }]);
