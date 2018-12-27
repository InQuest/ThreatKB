'use strict';

angular.module('ThreatKB')
    .controller('DashboardController', ['$scope', '$location', 'resolvedCfgCategoryRangeMapping', 'resolvedReleasesLatest', 'resolvedCfg_states', 'resolvedOwnershipData', 'resolvedBookmarks', 'resolvedVersion', 'Release',
        function ($scope, $location, resolvedCfgCategoryRangeMapping, resolvedReleasesLatest, resolvedCfg_states, resolvedOwnershipData, resolvedBookmarks, resolvedVersion, Release) {
            $scope.bookmarks = resolvedBookmarks;
            $scope.cfg_category_range_mapping = resolvedCfgCategoryRangeMapping;
            $scope.cfg_states = resolvedCfg_states;
            $scope.ownership_data = resolvedOwnershipData;
            $scope.latest_releases = resolvedReleasesLatest;
            $scope.version = resolvedVersion;

            $scope.customSearch = function(actual, expected) {
                if (expected.length < 3) {
                    return true;
                } else if (typeof actual !== "object") {
                    return actual.toString().toLowerCase().indexOf(expected.toString().toLowerCase()) !== -1;
                } else {
                    return false;
                }
            };

            $scope.getPermalink = function (prefix, id) {
                return $location.absUrl() + prefix + "/" + id;
            };
        }]);
