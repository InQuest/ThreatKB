'use strict';

angular.module('ThreatKB')
    .controller('TagsController', ['$scope', '$uibModal', 'resolvedTags', 'Tags',
        function ($scope, $uibModal, resolvedTags, Tags) {
            $scope.tags = resolvedTags;
            $scope.tag = {};

            $scope.customSearch = function(actual, expected) {
                if (expected.length < 3) {
                    return true;
                } else if (typeof actual !== "object") {
                    return actual.toString().toLowerCase().indexOf(expected.toString().toLowerCase()) !== -1;
                } else {
                    return false;
                }
            };

            $scope.create = function () {
                $scope.clear();
                $scope.open();
            };

            $scope.update = function (id) {
                $scope.tag = Tags.resource.get({id: id});
                $scope.tags = Tags.resource.query();
                $scope.open(id);
            };

            $scope.delete = function (id) {
                Tags.resource.delete({id: id},
                    function () {
                        $scope.tag = {};
                        $scope.tags = Tags.resource.query();
                    });
            };

            $scope.save = function (id) {
                if (id) {
                    Tags.resource.update({id: id}, $scope.tag,
                        function () {
                            $scope.tags = Tags.resource.query();
                        });
                } else {
                    Tags.resource.save($scope.tag,
                        function () {
                            $scope.tags = Tags.resource.query();
                        });
                }
            };

            $scope.clear = function () {
                $scope.tag = {
                    "text": "",
                    "id": ""
                };
            };

            $scope.open = function (id) {
                var tagsSave = $uibModal.open({
                    templateUrl: 'tags-save.html',
                    controller: 'TagsSaveController',
                    resolve: {
                        tag: function () {
                            return $scope.tag;
                        }
                    }
                });

                tagsSave.result.then(function (entity) {
                    $scope.tag = entity;
                    $scope.save(id);
                });
            };
        }])
    .controller('TagsSaveController', ['$scope', '$uibModalInstance', 'tag',
        function ($scope, $uibModalInstance, tag) {
            $scope.tag = tag;

            $scope.ok = function () {
                $uibModalInstance.close($scope.tag);
            };

            $scope.cancel = function () {
                $uibModalInstance.dismiss('cancel');
            };
        }]);
