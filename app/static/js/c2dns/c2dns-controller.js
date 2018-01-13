'use strict';

angular.module('ThreatKB')
    .controller('C2dnsController', ['$scope', '$timeout', '$filter', '$http', '$uibModal', 'resolvedC2dns', 'C2dns', 'Cfg_states', 'growl', 'Users', 'openModalForId', 'uiGridConstants',
        function ($scope, $timeout, $filter, $http, $uibModal, resolvedC2dns, C2dns, Cfg_states, growl, Users, openModalForId, uiGridConstants) {

            $scope.c2dns = resolvedC2dns;

            $scope.users = Users.query();

            $scope.cfg_states = Cfg_states.query();

            $scope.filterOptions = {
                filterText: ''
            };

            var paginationOptions = {
                pageNumber: 1,
                pageSize: 25,
                searches: {},
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

                        for (var i = 0; i < grid.columns.length; i++) {
                            var column = grid.columns[i];
                            if (column.filters[0].term !== undefined && column.filters[0].term !== null && column.filters[0].term !== "") {
                                paginationOptions.searches[column.colDef.field] = column.filters[0].term
                            }
                        }
                        getPage()
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
                        }, 500);
                    });
                },
                rowHeight: 35,
                columnDefs:
                    [
                        {field: 'domain_name'},
                        {field: 'match_type', enableSorting: true},
                        {field: 'expiration_type', enableSorting: true},
                        {
                            field: 'state',
                            displayName: 'State',
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
                            width: '20%',
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
                            name: 'Actions',
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
                            + '<button ng-click="grid.appScope.delete(row.entity.id)"'
                            + ' ng-confirm-click="Are you sure you want to '
                            + 'delete this c2dns?" class="btn btn-sm btn-danger">'
                            + '<small>'
                            + '<span class="glyphicon glyphicon-remove-circle"></span>'
                            + '</small>'
                            + '</button></div>'
                        }
                    ]
            };

            var getPage = function () {
                var url = '/ThreatKB/c2dns?';
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
                $scope.c2dns = C2dns.get({id: id});
                $scope.cfg_states = Cfg_states.query();
                $scope.users = Users.query();
                $scope.open(id);
            };

            $scope.delete = function (id) {
                C2dns.delete({id: id}, function () {
                    //$scope.c2dns = C2dns.query();
                    getPage();
                });
            };

            $scope.save = function (id_or_dns) {
                var id = id_or_dns;
                if (typeof(id_or_dns) === "object") {
                    id = id_or_dns.id;
                    $scope.c2dns = id_or_dns;
                }

                if (id) {
                    C2dns.update({id: id}, $scope.c2dns, function () {
                        //$scope.c2dns = C2dns.query();
                        getPage();
                    }, function (error) {
                        growl.error(error.data, {ttl: -1});
                    });
                } else {
                    $scope.c2dns.metadata_values = {};

                    if ($scope.c2dns.metadata[0].hasOwnProperty("string")) {
                        for (var i = 0; i < $scope.c2dns.metadata[0].string.length; i++) {
                            var entity = $scope.c2dns.metadata[0].string[i];
                            $scope.c2dns.metadata_values[entity.key] = {value: entity.default};
                        }
                    }
                    if ($scope.c2dns.metadata[0].hasOwnProperty("multiline_comment")) {
                        for (var i = 0; i < $scope.c2dns.metadata[0].multiline_comment.length; i++) {
                            var entity = $scope.c2dns.metadata[0].multiline_comment[i];
                            $scope.c2dns.metadata_values[entity.key] = {value: entity.default};
                        }
                    }

                    if ($scope.c2dns.metadata[0].hasOwnProperty("date")) {
                        for (var i = 0; i < $scope.c2dns.metadata[0].date.length; i++) {
                            var entity = $scope.c2dns.metadata[0].date[i];
                            $scope.c2dns.metadata_values[entity.key] = {value: entity.default};
                        }
                    }

                    if ($scope.c2dns.metadata[0].hasOwnProperty("integer")) {
                        for (var i = 0; i < $scope.c2dns.metadata[0].integer.length; i++) {
                            var entity = $scope.c2dns.metadata[0].integer[i];
                            $scope.c2dns.metadata_values[entity.key] = {value: entity.default};
                        }
                    }

                    if ($scope.c2dns.metadata[0].hasOwnProperty("select")) {
                        for (var i = 0; i < $scope.c2dns.metadata[0].select.length; i++) {
                            var entity = $scope.c2dns.metadata[0].select[i];
                            if (typeof(entity.default) == "object") {
                                $scope.c2dns.metadata_values[entity.key] = {value: entity.default.choice};
                            } else {
                                $scope.c2dns.metadata_values[entity.key] = {value: entity.default};
                            }
                        }
                    }

                    C2dns.save($scope.c2dns, function () {
                        //$scope.c2dns = C2dns.query();
                        getPage();
                    }, function (error) {
                        growl.error(error.data, {ttl: -1});
                    });
                }
            };

            $scope.clear = function () {
                $scope.c2dns = {
                    "date_created": "",
                    "date_modified": "",
                    "state": "",
                    "domain_name": "",
                    "match_type": "",
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
                var c2dnsSave = $uibModal.open({
                    templateUrl: 'c2dns-save.html',
                    controller: 'C2dnsSaveController',
                    size: 'lg',
                    backdrop: 'static',
                    resolve: {
                        c2dns: function () {
                            return $scope.c2dns;
                        },
                        metadata: ['Metadata', function (Metadata) {
                            return Metadata.query({
                                filter: "dns",
                                format: "dict"
                            });
                        }]
                    }
                });

                c2dnsSave.result.then(function (entity) {
                    $scope.c2dns = entity;
                    $scope.save(id);
                });
            };

            getPage();

            if (openModalForId !== null) {
                $scope.update(openModalForId);
            }
        }])
    .controller('C2dnsSaveController', ['$scope', '$http', '$uibModalInstance', '$location', 'c2dns', 'metadata', 'Cfg_states', 'Comments', 'Tags', 'growl', 'Bookmarks',
        function ($scope, $http, $uibModalInstance, $location, c2dns, metadata, Cfg_states, Comments, Tags, growl, Bookmarks) {
            $scope.c2dns = c2dns;
            $scope.c2dns.new_comment = "";
            $scope.Comments = Comments;
            $scope.metadata = metadata;
            if (!$scope.c2dns.id) {
                $scope.c2dns.metadata = metadata;
            }

            $scope.update_selected_metadata = function (m, selected) {
                if (!$scope.c2dns.metadata_values[m.key]) {
                    $scope.c2dns.metadata_values[m.key] = {};
                }
                $scope.c2dns.metadata_values[m.key].value = selected.choice;
            };

            if ($scope.c2dns.$promise !== undefined) {
                $scope.c2dns.$promise.then(function (result) {
                }, function (errorMsg) {
                    growl.error("Task Not Found", {ttl: -1});
                    $uibModalInstance.dismiss('cancel');
                });
            }

            $scope.bookmark = function (id) {
                Bookmarks.createBookmark(Bookmarks.ENTITY_MAPPING.DNS, id).then(function (data) {
                    $scope.c2dns.bookmarked = true;
                });
            };

            $scope.unbookmark = function (id) {
                Bookmarks.deleteBookmark(Bookmarks.ENTITY_MAPPING.DNS, id).then(function (data) {
                    $scope.c2dns.bookmarked = false;
                });
            };

            $scope.getPermalink = function (id) {
                return $location.absUrl() + "/" + id;
            };

            $scope.match_types = ['exact', 'wildcard'];
            if (!$scope.c2dns.match_type) {
                $scope.c2dns.match_type = $scope.match_types[0];
            }

            $scope.cfg_states = Cfg_states.query();

            $scope.print_comment = function (comment) {
                return comment.comment.replace(/(?:\r\n|\r|\n)/g, "<BR>");
            };

            $scope.add_comment = function (id) {
                if (!$scope.c2dns.new_comment) {
                    return;
                }

                $scope.Comments.resource.save({
                    comment: $scope.c2dns.new_comment,
                    entity_type: Comments.ENTITY_MAPPING.DNS,
                    entity_id: id
                }, function () {
                    $scope.c2dns.new_comment = "";
                    $scope.c2dns.comments = $scope.Comments.resource.query({
                        entity_type: Comments.ENTITY_MAPPING.DNS,
                        entity_id: id
                    })
                });
            };

            $scope.ok = function () {
                $uibModalInstance.close($scope.c2dns);
            };

            $scope.cancel = function () {
                $uibModalInstance.dismiss('cancel');
            };

            $scope.addedTag = function ($tag) {
                $scope.c2dns.addedTags.push($tag)
            };

            $scope.removedTag = function ($tag) {
                $scope.c2dns.removedTags.push($tag)
            };

            $scope.loadTags = function (query) {
                return Tags.loadTags(query);
            };
        }]);
