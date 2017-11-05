'use strict';

angular.module('ThreatKB')
    .controller('DashboardController', ['$scope', 'resolvedCfgCategoryRangeMapping', 'resolvedCfg_states', 'resolvedOwnershipData', 'resolvedReleaseLatest',
        function ($scope, resolvedCfgCategoryRangeMapping, resolvedCfg_states, resolvedOwnershipData, resolvedReleaseLatest) {

            $scope.cfg_category_range_mapping = resolvedCfgCategoryRangeMapping;
            $scope.cfg_states = resolvedCfg_states;
            $scope.ownership_data = resolvedOwnershipData;
            $scope.latest_release = resolvedReleaseLatest;

        }])
