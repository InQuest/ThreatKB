'use strict';

angular.module('ThreatKB')
    .controller('ActivityLogController', ['$scope', '$location', '$timeout', '$filter', '$http', 'resolvedActivityLog', 'ActivityLog', 'uiGridConstants', '$routeParams', 'Cfg_settings', 'Users',
        function ($scope, $location, $timeout, $filter, $http, resolvedActivityLog, ActivityLog, uiGridConstants, $routeParams, Cfg_settings, Users) {

            $scope.activity_logs = resolvedActivityLog;

            $scope.users = Users.query();

            $scope.filterOptions = {
                filterText: ''
            };

            $scope.start_filter_requests_length = Cfg_settings.get({key: "START_FILTER_REQUESTS_LENGTH"});

            $scope.searches = {};
            if ($routeParams.searches) {
                $scope.searches = JSON.parse($routeParams.searches);
            }

            $scope.getPermalink = function (entity_type, id) {
                var permalink = $location.absUrl().substring(0, $location.absUrl().indexOf($location.url()))
                    + "/" + ActivityLog.PERMALINK_MAPPING[entity_type];
                if (entity_type !== "RELEASE") {
                    permalink += "/" + id;
                }
                return permalink;
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
                        var trigger_refresh_for_selection = false;

                        for (var i = 0; i < grid.columns.length; i++) {
                            var column = grid.columns[i];
                            trigger_refresh_for_emptiness &= (column.filters[0].term === undefined || column.filters[0].term === null || column.filters[0].term.length === 0);

                            if (column.filters[0].term !== undefined && column.filters[0].term !== null) {
                                if (column.field === "entity_type" || column.field === "activity_type") {
                                    trigger_refresh_for_selection = true;
                                    paginationOptions.searches[column.colDef.field] = column.filters[0].term;
                                } else if ("~" === column.filters[0].term
                                    || column.filters[0].term.length >= parseInt($scope.start_filter_requests_length.value)) {
                                    trigger_refresh_for_length = true;
                                    paginationOptions.searches[column.colDef.field] = column.filters[0].term;
                                }
                            }
                        }
                        if (trigger_refresh_for_length || trigger_refresh_for_emptiness || trigger_refresh_for_selection) {
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
                            $('[role="rowgroup"]').css('overflow', 'auto');
                        }, 500);
                    });
                },
                rowHeight: 35,
                columnDefs:
                    [
                        {
                            field: 'activity_type',
                            displayName: 'Activity Type',
                            enableSorting: true,
                            width: '165',
                            filterHeaderTemplate: '<div class="ui-grid-filter-container" ng-repeat="colFilter in col.filters">'
                                + '<ui-select append-to-body="true" ng-model="colFilter.term">'
                                + '<ui-select-match allow-clear="true">'
                                + '<small><span ng-bind="$select.selected.label || colFilter.term"></span></small>'
                                + '</ui-select-match>'
                                + '<ui-select-choices repeat="option.value as option in colFilter.options">'
                                + '<small><span ng-bind="option.label"></span></small>'
                                + '</ui-select-choices>'
                                + '</ui-select>'
                                + '</div>',
                            filter: {
                                type: uiGridConstants.filter.SELECT,
                                options: [
                                    {value: "ARTIFACT_CREATED", label: "Artifact Created"},
                                    {value: "ARTIFACT_MODIFIED", label: "Artifact Modified"},
                                    {value: "COMMENTS", label: 'Comment'},
                                    {value: "STATE_TOGGLED", label: 'State Toggled'},
                                    {value: "RELEASES_MADE", label: 'Release Made'}
                                ]
                            }
                        },
                        {
                            field: 'entity_type',
                            displayName: 'Entity Type',
                            enableSorting: true,
                            width: '160',
                            filterHeaderTemplate: '<div class="ui-grid-filter-container" ng-repeat="colFilter in col.filters">'
                                + '<ui-select append-to-body="true" ng-model="colFilter.term">'
                                + '<ui-select-match allow-clear="true">'
                                + '<small><span ng-bind="$select.selected.label || colFilter.term"></span></small>'
                                + '</ui-select-match>'
                                + '<ui-select-choices repeat="option.value as option in colFilter.options">'
                                + '<small><span ng-bind="option.label"></span></small>'
                                + '</ui-select-choices>'
                                + '</ui-select>'
                                + '</div>',
                            filter: {
                                type: uiGridConstants.filter.SELECT,
                                options: [
                                    {value: '2', label: 'DNS'},
                                    {value: '3', label: 'IP'},
                                    {value: '1', label: 'SIGNATURE'},
                                    {value: '4', label: 'TASK'},
                                    {value: '5', label: 'RELEASE'}
                                ]
                            }
                        },
                        {
                            field: 'activity_date',
                            displayName: 'Activity Date',
                            enableSorting: true,
                            width: '150',
                            cellFilter: 'date:\'yyyy-MM-dd HH:mm:ss\''
                        },
                        {
                            field: 'activity_text',
                            displayName: 'Activity Text',
                            enableSorting: true,
                            cellClass: 'grid-align',
                            cellTemplate: '<a target="_blank" title="{{ row.entity.activity_text }}"'
                                + ' href="{{ grid.appScope.getPermalink(row.entity.entity_type, row.entity.entity_id) }}">'
                                + '{{ row.entity.activity_text }}'
                                + '</a>'
                        },
                        {
                            field: 'user.email',
                            displayName: 'Activity User',
                            enableSorting: true,
                            width: 170,
                            cellTemplate: '<span>{{row.entity.user.email}}</span>'
                        }
                    ]
            };

            var getPage = function () {
                var url = '/ThreatKB/activity_log?';
                url += 'page_number=' + (paginationOptions.pageNumber - 1);
                url += '&page_size=' + paginationOptions.pageSize;
                url += '&since=45';
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
                $http.get(url).then(function (response) {
                    $scope.gridOptions.totalItems = response.data.total_count;
                    $scope.gridOptions.data = response.data.data;
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
        }]);
