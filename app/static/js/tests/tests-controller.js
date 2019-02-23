'use strict';

angular.module('ThreatKB')
    .controller('TestsController', ['$scope', '$timeout', '$filter', '$http', '$uibModal', 'resolvedTests', 'growl', 'uiGridConstants', '$routeParams', '$location', 'Cfg_settings', 'Tests',
        function ($scope, $timeout, $filter, $http, $uibModal, resolvedTests, growl, uiGridConstants, $routeParams, $location, Cfg_settings, Tests) {

            $scope.tests = resolvedTests;

            $scope.start_filter_requests_length = Cfg_settings.get({key: "START_FILTER_REQUESTS_LENGTH"});

            $scope.searches = {};
            if ($routeParams.searches) {
                $scope.searches = JSON.parse($routeParams.searches);
            }

            $scope.filterOptions = {
                filterText: ''
            };

            var paginationOptions = {
                pageNumber: 1,
                pageSize: 25,
                searches: $scope.searches,
                sort_by: null,
                sort_dir: null
            };


            $scope.gridOptions = {
                paginationPageSizes: [25, 50, 75, 100],
                paginationPageSize: 25,
                useExternalFiltering: true,
                useExternalPagination: true,
                useExternalSorting: true,
                enableFiltering: true,
                flatEntityAccess: true,
                fastWatch: true,
                onRegisterApi: function (gridApi) {
                    $scope.gridApi = gridApi;
                    $scope.gridApi.core.on.filterChanged($scope, function () {
                        var grid = this.grid;
                        paginationOptions.searches = {};
                        var trigger_refresh_for_length = false;
                        var trigger_refresh_for_emptiness = true;

                        for (var i = 0; i < grid.columns.length; i++) {
                            var column = grid.columns[i];
                            trigger_refresh_for_emptiness &= (column.filters[0].term === undefined || column.filters[0].term === null || column.filters[0].term.length === 0);

                            if (column.filters[0].term !== undefined && column.filters[0].term !== null && column.filters[0].term.length >= parseInt($scope.start_filter_requests_length.value)) {
                                trigger_refresh_for_length = true;
                                paginationOptions.searches[column.colDef.field] = column.filters[0].term
                            }
                        }
                        if (trigger_refresh_for_length || trigger_refresh_for_emptiness) {
                            getPage();
                        }
                    });
                    $scope.gridApi.core.on.sortChanged($scope, function (grid, sortColumns) {
                        if (sortColumns.length === 0) {
                            paginationOptions.sort_dir = null;
                        } else {
                            paginationOptions.sort_by = sortColumns[0].colDef.field;
                            paginationOptions.sort_dir = sortColumns[0].sort.direction;
                        }
                        getPage();
                    });
                    gridApi.pagination.on.paginationChanged($scope, function (newPage, pageSize) {
                        paginationOptions.pageNumber = newPage;
                        paginationOptions.pageSize = pageSize;
                        getPage();
                    });
                    gridApi.core.on.renderingComplete($scope, function () {
                        $timeout(function () {
                            $("div").each(function () {
                                $(this).removeAttr("tabindex");
                            });
                            $("span").each(function () {
                                $(this).removeAttr("tabindex");
                            });
                            $("input").each(function () {
                                $(this).removeAttr("tabindex");
                            });
                            $(":input[type=text]").each(function (i) {
                                if ($(this).hasClass("ui-grid-filter-input")) {
                                    $(this).attr("tabindex", i + 1);
                                    if ((i + 1) === 1) {
                                        $(this).focus();
                                    }
                                }
                            });
                            $('[role="rowgroup"]').css('overflow', 'auto');     // Force "rowgroup" container to hide horizontal scroll when not needed and allow for height to be precisely calculated
                        }, 500);
                    });
                },
                rowHeight: 35,
                columnDefs:
                    [
                        {
                            field: 'id',
                            displayName: 'ID',
                            width: 60,
                            enableFiltering: false
                        },
                        {
                            field: 'test_type',
                            displayName: "Test Type",
                            enableSorting: true,
                            width: 90
                        },
                        {
                            field: 'status',
                            displayName: "Status",
                            enableSorting: true,
                            width: 90
                        },
                        {
                            field: 'yara_rule_name',
                            enableSorting: true,
                            displayName: "Yara Rule",
                            cellTemplate: '<div class="text-left" style="padding-left:10px;">' +
                            '<a href=\'/#!/yara_rules/{{row.entity.yara_rule_id}}\' target="_blank">{{row.entity.yara_rule_name}}</a> : {{row.entity.revision}}' +
                            '</div>',
                            width: 375
                        },
                        {
                            field: 'start_time',
                            displayName: "Start Time",
                            width: 150
                        },
                        {
                            field: 'end_time',
                            displayName: "End Time",
                            width: 150
                        },
                        {
                            field: 'files_tested',
                            displayName: "Tested",
                            width: 85
                        },
                        {
                            field: 'files_matched',
                            displayName: "Matched",
                            width: 85
                        },
                        {
                            field: 'avg_millis_per_file',
                            displayName: "Runtime Avg",
                            width: 120
                        },
                        {
                            field: 'user_email',
                            displayName: 'Created By'
                        },
                        {
                            name: 'Matches',
                            width: '80',
                            enableFiltering: false,
                            enableColumnMenu: false,
                            enableSorting: false,
                            cellTemplate: '<div style="text-align: center;">'
                            + '<button type="button" ng-click="grid.appScope.viewResults(row.entity.id)"'
                            + ' class="btn btn-sm">'
                            + '<small><span class="glyphicon glyphicon-eye-open"></span>'
                            + '</small>'
                            + '</button>'
                            + '</div>'
                        }
                    ]
            };

            $scope.viewResults = function (id) {
                $scope.test = Tests.resource.get({id: id});
                $scope.view(id);
            };

            $scope.view = function (id) {
                var test_resultsview = $uibModal.open({
                    templateUrl: 'test_results_matches-view.html',
                    controller: 'Test_resultsViewController',
                    size: 'lg',
                    backdrop: 'static',
                    resolve: {
                        test: function () {
                            return $scope.test;
                        }
                    }
                });
            };


            var getPage = function () {
                var url = '/ThreatKB/tests?';
                url += 'page_number=' + (paginationOptions.pageNumber - 1);
                url += '&page_size=' + paginationOptions.pageSize;
                switch (paginationOptions.sort_dir) {
                    case uiGridConstants.ASC:
                        url += '&sort_dir=ASC';
                        break;
                    case uiGridConstants.DESC:
                        url += '&sort_dir=DESC';
                        break;
                    default:
                        break;
                }
                if (paginationOptions.sort_by !== null) {
                    url += '&sort_by=' + paginationOptions.sort_by;
                }
                if (paginationOptions.searches !== {}) {
                    url += '&searches=' + JSON.stringify(paginationOptions.searches);
                }
                $http.get(url)
                    .then(function (response) {
                        $scope.gridOptions.totalItems = response.data.total_count;
                        $scope.gridOptions.data = response.data.data;
                        $scope.tests = $scope.gridOptions.data;
                        $scope.clear_checked();
                        for (var i = 0; i < $scope.gridOptions.data.length; i++) {
                            $scope.checked_indexes.push(false);
                        }
                        $scope.gridApi.grid.gridHeight = parseInt($scope.getTableHeight().height);  // Re-apply table height calculation, based on new data
                        $scope.gridApi.core.refresh();
                    }, function (error) {
                    });
            };

            $scope.getTableHeight = function () {
                var rowHeight = $scope.gridOptions.rowHeight;
                var headerHeight = 100;
                return {
                    height: ($scope.gridOptions.data.length * rowHeight + headerHeight) + "px"
                };
            };

            getPage();

        }])
    .controller('Test_resultsViewController', ['$scope', '$http', '$uibModalInstance', '$location', 'test', 'Comments', 'blockUI',
        function ($scope, $http, $uibModalInstance, $location, test, growl, blockUI) {
            $scope.test = test;

            if ($scope.test.$promise !== undefined) {
                $scope.test.$promise.then(function (result) {
                }, function (errorMsg) {
                    growl.error("Test Not Found", {ttl: -1});
                    $uibModalInstance.dismiss('cancel');
                });
            }

            angular.element(document.body).toggleClass('modals-full-screen');

            $scope.ok = function () {
                $uibModalInstance.close($scope.test);
            };

            $scope.cancel = function () {
                $uibModalInstance.dismiss('cancel');
            };
        }]);
