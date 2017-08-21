'use strict';

angular.module('InquestKB')
    .controller('FilesController', ['$scope', '$uibModal', 'resolvedFiles', 'Files',
        function ($scope, $uibModal, resolvedFiles, Files) {

            $scope.files = resolvedFiles;

            $scope.create = function () {
                $scope.clear();
                $scope.open();
            };

            $scope.update = function (id) {
                $scope.files = Files.get({id: id});
                $scope.open(id);
            };

            $scope.delete = function (id) {
                Files.delete({id: id}, function () {
                    $scope.files = Files.query();
                });
            };

            $scope.save = function (id) {
                if (id) {
                    Files.update({id: id}, $scope.files, function () {
                        $scope.files = Files.query();
                    });
                } else {
                    Files.save($scope.files, function () {
                        $scope.files = Files.query();
                    });
                }
            };

            $scope.clear = function () {
                $scope.files = {
                    "filename": "",
                    "content_type": "",
                    "id": ""
                };
            };

            $scope.open = function (id) {
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
                    $scope.save(id);
                });
            };
        }])
    .controller('FilesSaveController', ['$scope', '$uibModalInstance', 'files',
        function ($scope, $uibModalInstance, files) {
            $scope.files = files;

            $scope.ok = function () {
                $uibModalInstance.close($scope.files);
            };

            $scope.cancel = function () {
                $uibModalInstance.dismiss('cancel');
            };
        }]);
