'use strict';

angular.module('InquestKB')
    .controller('ReleaseController', ['$scope', '$uibModal', 'resolvedYara_rule', 'Release',
        function ($scope, $uibModal, resolvedRelease, Release) {

            $scope.releases = resolvedRelease;

            $scope.create = function () {
                $scope.clear();
                $scope.open();
            };

            $scope.delete = function (id) {
                Release.delete({id: id}, function () {
                    $scope.releases = Release.query();
                });
            };

            $scope.save = function (id) {
                if (id) {
                    Release.update({id: id}, $scope.release, function () {
                        $scope.releases = Release.query();
                    });
                } else {
                    Release.save($scope.release, function () {
                        $scope.releases = Release.query();
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
                    size: 'sm',
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

            $scope.get_release_notes = function (id) {

            };
        }
    ])
    .controller('ReleaseSaveController', ['$scope', '$http', '$uibModalInstance', 'Release',
        function ($scope, $http, $uibModalInstance, Release) {
            $scope.release = release;

            $scope.ok = function () {
                $uibModalInstance.close($scope.release);
            };

            $scope.cancel = function () {
                $uibModalInstance.dismiss('cancel');
            };

        }]);
