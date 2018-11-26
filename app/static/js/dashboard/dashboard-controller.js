'use strict';

angular.module('ThreatKB')
    .controller('DashboardController', ['$scope', '$location', 'resolvedCfgCategoryRangeMapping', 'resolvedCfg_states', 'resolvedOwnershipData', 'resolvedReleasesLatest', 'resolvedBookmarks', 'resolvedVersion',
        function ($scope, $location, resolvedCfgCategoryRangeMapping, resolvedCfg_states, resolvedOwnershipData, resolvedReleasesLatest, resolvedBookmarks, resolvedVersion) {
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
