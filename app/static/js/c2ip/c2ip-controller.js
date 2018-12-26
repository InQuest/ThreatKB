'use strict';

angular.module('ThreatKB')
    .controller('C2ipController', ['$scope', '$timeout', '$filter', '$http', '$uibModal', 'resolvedC2ip', 'C2ip', 'Cfg_states', 'growl', 'Users', 'openModalForId', 'uiGridConstants', 'Cfg_settings', '$routeParams',
        function ($scope, $timeout, $filter, $http, $uibModal, resolvedC2ip, C2ip, Cfg_states, growl, Users, openModalForId, uiGridConstants, Cfg_settings, $routeParams) {

            $scope.c2ips = resolvedC2ip;

            $scope.users = Users.query();

            $scope.start_filter_requests_length = Cfg_settings.get({key: "START_FILTER_REQUESTS_LENGTH"});

            $scope.cfg_states = Cfg_states.query();

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
                                    if ((i + 1) == 1) {
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
                            field: 'ip',
                            displayName: 'IP',
                            width: '220',
                            enableSorting: true
                        },
                        {
                            field: 'date_created',
                            displayName: "Created Date",
                            enableSorting: true,
                            width: '150',
                            cellFilter: 'date:\'yyyy-MM-dd HH:mm:ss\''
                        },
                        {
                            field: 'description',
                            enableSorting: true
                        },
                        {
                            field: 'state',
                            displayName: 'State',
                            width: '130',
                            enableSorting: true,
                            cellTemplate: '<ui-select append-to-body="true" ng-model="row.entity.state"'
                            + ' on-select="grid.appScope.save(row.entity)">'
                            + '<ui-select-match placeholder="Select an state ...">'
                            + '<small><span ng-bind="$select.selected.state || row.entity.state"></span></small>'
                            + '</ui-select-match>'
                            + '<ui-select-choices'
                            + ' repeat="state in (grid.appScope.cfg_states | filter: $select.search) track by state.id">'
                            + '<small><span ng-bind="state.state"></span></small>'
                            + '</ui-select-choices>'
                            + '</ui-select>'
                            + '</div>'
                        },
                        {
                            field: 'owner_user.email',
                            displayName: 'Owner',
                            width: '170',
                            enableSorting: false,
                            cellTemplate: '<ui-select append-to-body="true" ng-model="row.entity.owner_user"'
                            + ' on-select="grid.appScope.save(row.entity)">'
                            + '<ui-select-match placeholder="Select an owner ...">'
                            + '<small><span ng-bind="$select.selected.email || row.entity.owner_user.email"></span></small>'
                            + '</ui-select-match>'
                            + '<ui-select-choices'
                            + ' repeat="person in (grid.appScope.users | filter: $select.search) track by person.id">'
                            + '<small><span ng-bind="person.email"></span></small>'
                            + '</ui-select-choices>'
                            + '</ui-select>'
                            + '</div>'
                        },
                        {
                            field: 'tags',
                            displayName: 'Tags',
                            width: '180',
                            enableSorting: false,
                            cellTemplate: '<ul class="gridTags" append-to-body="true" ng-model="row.entity.tags">'
                            + '<li ng-repeat="tag in (row.entity.tags | filter: $select.search) track by tag.id">'
                            + '<small>{{tag.text}}</small>'
                            + '</li>'
                            + '</ul>'
                            + '</div>'
                        },
                        {
                            name: 'Actions',
                            width: '120',
                            enableFiltering: false,
                            enableColumnMenu: false,
                            enableSorting: false,
                            cellTemplate: '<div style="text-align: center;">'
                            + '<button type="button" ng-click="grid.appScope.update(row.entity.id)"'
                            + ' class="btn btn-sm">'
                            + '<small><span class="glyphicon glyphicon-pencil"></span>'
                            + '</small>'
                            + '</button>'
                            + '&nbsp;'
                            + '<button confirmed-click="grid.appScope.delete(row.entity.id)"'
                            + ' ng-confirm-click="Are you sure you want to '
                            + 'delete this c2ip?" class="btn btn-sm btn-danger">'
                            + '<small>'
                            + '<span class="glyphicon glyphicon-remove-circle"></span>'
                            + '</small>'
                            + '</button></div>'
                        }
                    ]
            };

            var getPage = function () {
                var url = '/ThreatKB/c2ips?';
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

            $scope.create = function () {
                $scope.clear();
                $scope.open();
            };

            $scope.update = function (id) {
                $scope.c2ip = C2ip.get({id: id});
                $scope.cfg_states = Cfg_states.query();
                $scope.users = Users.query();
                $scope.open(id);
            };

            $scope.delete = function (id) {
                C2ip.delete({id: id}, function () {
                    //$scope.c2ips = C2ip.query();
                    getPage();
                });
            };

            $scope.save = function (id_or_ip) {
                var id = id_or_ip;
                if (typeof(id_or_ip) === "object") {
                    id = id_or_ip.id;
                    $scope.c2ip = id_or_ip;
                }

                if (id) {
                    C2ip.update({id: id}, $scope.c2ip, function () {
                        //$scope.c2ips = C2ip.query();
                        getPage();
                    }, function (error) {
                        growl.error(error.data, {ttl: -1});
                    });
                } else {
                    $scope.c2ip.metadata_values = {};

                    if ($scope.c2ip.metadata[0].hasOwnProperty("string")) {
                        for (var i = 0; i < $scope.c2ip.metadata[0].string.length; i++) {
                            var entity = $scope.c2ip.metadata[0].string[i];
                            $scope.c2ip.metadata_values[entity.key] = {value: entity.default};
                        }
                    }
                    if ($scope.c2ip.metadata[0].hasOwnProperty("multiline_comment")) {
                        for (var i = 0; i < $scope.c2ip.metadata[0].multiline_comment.length; i++) {
                            var entity = $scope.c2ip.metadata[0].multiline_comment[i];
                            $scope.c2ip.metadata_values[entity.key] = {value: entity.default};
                        }
                    }

                    if ($scope.c2ip.metadata[0].hasOwnProperty("date")) {
                        for (var i = 0; i < $scope.c2ip.metadata[0].date.length; i++) {
                            var entity = $scope.c2ip.metadata[0].date[i];
                            $scope.c2ip.metadata_values[entity.key] = {value: entity.default};
                        }
                    }

                    if ($scope.c2ip.metadata[0].hasOwnProperty("integer")) {
                        for (var i = 0; i < $scope.c2ip.metadata[0].integer.length; i++) {
                            var entity = $scope.c2ip.metadata[0].integer[i];
                            $scope.c2ip.metadata_values[entity.key] = {value: entity.default};
                        }
                    }

                    if ($scope.c2ip.metadata[0].hasOwnProperty("select")) {
                        for (var i = 0; i < $scope.c2ip.metadata[0].select.length; i++) {
                            var entity = $scope.c2ip.metadata[0].select[i];
                            if (typeof(entity.default) == "object") {
                                $scope.c2ip.metadata_values[entity.key] = {value: entity.default.choice};
                            } else {
                                $scope.c2ip.metadata_values[entity.key] = {value: entity.default};
                            }
                        }
                    }

                    C2ip.save($scope.c2ip, function () {
                        //$scope.c2ips = C2ip.query();
                        getPage();
                    }, function (error) {
                        growl.error(error.data, {ttl: -1});
                    });
                }
            };

            $scope.clear = function () {
                $scope.c2ip = {
                    "date_created": "",
                    "date_modified": "",
                    "state": "",
                    "ip": "",
                    "asn": "",
                    "country": "",
                    "reference_link": "",
                    "expiration_type": "",
                    "expiration_timestamp": "",
                    "description": "",
                    "id": "",
                    "tags": [],
                    "addedTags": [],
                    "removedTags": []
                };
            };

            $scope.open = function (id) {
                var c2ipSave = $uibModal.open({
                    templateUrl: 'c2ip-save.html',
                    controller: 'C2ipSaveController',
                    size: 'lg',
                    backdrop: 'static',
                    resolve: {
                        c2ip: function () {
                            return $scope.c2ip;
                        },
                        metadata: ['Metadata', function (Metadata) {
                            return Metadata.query({
                                filter: "ip",
                                format: "dict"
                            });
                        }]
                    }
                });

                c2ipSave.result.then(function (entity) {
                    $scope.c2ip = entity;
                    $scope.save(id);
                }, function () {
                    getPage();
                });
            };

            getPage();

            if (openModalForId !== null) {
                $scope.update(openModalForId);
            }
        }])
    .controller('C2ipSaveController', ['$scope', '$http', '$uibModalInstance', '$location', 'C2ip', 'c2ip', 'metadata', 'Comments', 'Cfg_states', 'Tags', 'growl', 'Bookmarks', 'hotkeys', 'Users',
        function ($scope, $http, $uibModalInstance, $location, C2ip, c2ip, metadata, Comments, Cfg_states, Tags, growl, Bookmarks, hotkeys, Users) {
            $scope.c2ip = c2ip;
            if (!$scope.c2ip.id) {
                $scope.c2ip.metadata = metadata;
            }
            $scope.c2ip.new_comment = "";
            $scope.Comments = Comments;
            $scope.metadata = metadata;

            $scope.users = Users.query();

            $scope.save_artifact = function () {
                C2ip.update({id: $scope.c2ip.id}, $scope.c2ip,
                    function (data) {
                        if (!data) {
                            growl.error(error, {ttl: -1});
                        } else {
                            growl.info("Successfully saved dns artifact '" + $scope.c2ip.ip + "'.", {ttl: 2000});
                        }
                    });
            };

            hotkeys.bindTo($scope)
                .add({
                    combo: 'ctrl+s',
                    description: 'Save',
                    allowIn: ['INPUT', 'SELECT', 'TEXTAREA'],
                    callback: function () {
                        $scope.save_artifact();
                    }
                }).add({
                combo: 'ctrl+q',
                description: 'Escape',
                allowIn: ['INPUT', 'SELECT', 'TEXTAREA'],
                callback: function () {
                    $scope.cancel();
                }
            });

            $scope.update_selected_metadata = function (m, selected) {
                if (!$scope.c2ip.metadata_values[m.key]) {
                    $scope.c2ip.metadata_values[m.key] = {};
                }
                $scope.c2ip.metadata_values[m.key].value = selected.choice;
            };

            if ($scope.c2ip.$promise !== undefined) {
                $scope.c2ip.$promise.then(function (result) {
                }, function (errorMsg) {
                    growl.error("C2ip Not Found", {ttl: -1});
                    $uibModalInstance.dismiss('cancel');
                });
            }

            $scope.bookmark = function (id) {
                Bookmarks.createBookmark(Bookmarks.ENTITY_MAPPING.IP, id).then(function (data) {
                    $scope.c2ip.bookmarked = true;
                });
            };

            $scope.unbookmark = function (id) {
                Bookmarks.deleteBookmark(Bookmarks.ENTITY_MAPPING.IP, id).then(function (data) {
                    $scope.c2ip.bookmarked = false;
                });
            };

            $scope.getPermalink = function (id) {
                var location = $location.absUrl();
                var last_spot = location.split("/")[location.split("/").length - 1]
                if (isNaN(parseInt(last_spot, 10))) {
                    return $location.absUrl() + "/" + id;
                } else if (!isNaN(parseInt(last_spot, 10)) && last_spot != id) {
                    return $location.absUrl().replace(/\/[0-9]+$/, "/" + id)
                }
                return $location.absUrl();
            };


            $scope.cfg_states = Cfg_states.query();

            $scope.print_comment = function (comment) {
                return comment.comment.replace(/(?:\r\n|\r|\n)/g, "<BR>");
            };

            $scope.add_comment = function (id) {
                if (!$scope.c2ip.new_comment) {
                    return;
                }

                $scope.Comments.resource.save({
                    comment: $scope.c2ip.new_comment,
                    entity_type: Comments.ENTITY_MAPPING.IP,
                    entity_id: id
                }, function () {
                    $scope.c2ip.new_comment = "";
                    $scope.c2ip.comments = $scope.Comments.resource.query({
                        entity_type: Comments.ENTITY_MAPPING.IP,
                        entity_id: id
                    })
                });
            };

            $scope.ok = function () {
                $uibModalInstance.close($scope.c2ip);
            };

            $scope.cancel = function () {
                $uibModalInstance.dismiss('cancel');
            };

            $scope.addedTag = function ($tag) {
                $scope.c2ip.addedTags.push($tag)
            };

            $scope.removedTag = function ($tag) {
                $scope.c2ip.removedTags.push($tag)
            };

            $scope.loadTags = function (query) {
                return Tags.loadTags(query);
            };
        }]);
