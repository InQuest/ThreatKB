'use strict';

angular.module('InquestKB')
    .controller('FilesController', ['$scope', '$uibModal', 'resolvedFiles', 'Files',
        function ($scope, $uibModal, resolvedFiles, Files) {

            $scope.files = resolvedFiles;

            $scope.create = function () {
                $scope.open();
            };

            $scope.delete = function (id) {
                Files.resource.delete({id: id}, function () {
                    $scope.files = Files.resource.query();
                });
            };

            $scope.refresh = function () {
                $scope.files = Files.resource.query();
            };

            $scope.open = function () {
                var filesSave = $uibModal.open({
                    templateUrl: 'files-save.html',
                    controller: 'FilesSaveController',
                    resolve: {
                        files: function () {
                            return $scope.files;
                        }
                    }
                });

                filesSave.result.then(function (entity) {
                    $scope.files = entity;
                    $scope.refresh();
                });
            };
        }])
    .controller('FilesSaveController', ['$scope', '$uibModalInstance', 'files', 'growl', 'Upload',
        function ($scope, $uibModalInstance, files, growl, Upload) {
            $scope.files = files;

            $scope.ok = function () {
                $uibModalInstance.close($scope.files);
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
                                url: '/InquestKB/file_upload',
                                method: 'POST',
                                data: {
                                    file: file
                                }
                            }).then(function (resp) {
                                growl.info('Success ' + resp.config.data.file.name + ' uploaded.', {ttl: 3000});
                            }, function (resp) {
                                growl.info('Error status: ' + resp.status, {ttl: 3000});
                            }, function (evt) {
                                var progressPercentage = parseInt(100.0 * evt.loaded / evt.total);
                                console.log('progress: ' + progressPercentage + '% ' + evt.config.data.file.name);
                            });
                        }
                    }
                }
            };
        }]);
