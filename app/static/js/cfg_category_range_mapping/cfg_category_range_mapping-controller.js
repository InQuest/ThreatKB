'use strict';

angular.module('ThreatKB')
    .controller('CfgCategoryRangeMappingController', ['$scope', '$uibModal', 'resolvedCfgCategoryRangeMapping', 'CfgCategoryRangeMapping',
        function ($scope, $uibModal, resolvedCfgCategoryRangeMapping, CfgCategoryRangeMapping) {

            $scope.cfg_category_range_mapping = resolvedCfgCategoryRangeMapping;

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
                $scope.cfg_category_range_mapping = CfgCategoryRangeMapping.get({id: id});
                $scope.open(id);
            };

            $scope.delete = function (id) {
                CfgCategoryRangeMapping.delete({id: id},
                    function () {
                        $scope.cfg_category_range_mapping = CfgCategoryRangeMapping.query();
                    });
            };

            $scope.save = function (id) {
                if (id) {
                    CfgCategoryRangeMapping.update({id: id}, $scope.cfg_category_range_mapping,
                        function () {
                            $scope.cfg_category_range_mapping = CfgCategoryRangeMapping.query();
                        });
                } else {
                    CfgCategoryRangeMapping.save($scope.cfg_category_range_mapping,
                        function () {
                            $scope.cfg_category_range_mapping = CfgCategoryRangeMapping.query();
                        }, function (error) {
                            growl.error(error.data, {ttl: -1});
                        })
                }
            };

            $scope.clear = function () {
                $scope.cfg_category_range_mapping = {
                    "category": "",
                    "range_min": "",
                    "range_max": "",
                    "current": "",
                    "id": ""
                };
            };

            $scope.open = function (id) {
                var CfgCategoryRangeMappingSave = $uibModal.open({
                    templateUrl: 'cfg_category_range_mapping-save.html',
                    controller: 'CfgCategoryRangeMappingSaveController',
                    resolve: {
                        cfg_category_range_mapping: function () {
                            return $scope.cfg_category_range_mapping;
                        }
                    }
                });

                CfgCategoryRangeMappingSave.result.then(function (entity) {
                    $scope.cfg_category_range_mapping = entity;
                    $scope.save(id);
                });
            };
        }])
    .controller('CfgCategoryRangeMappingSaveController', ['$scope', '$uibModalInstance', 'cfg_category_range_mapping',
        function ($scope, $uibModalInstance, cfg_category_range_mapping) {
            $scope.cfg_category_range_mapping = cfg_category_range_mapping;

            $scope.ok = function () {
                $uibModalInstance.close($scope.cfg_category_range_mapping);
            };

            $scope.cancel = function () {
                $uibModalInstance.dismiss('cancel');
            };
        }]);
