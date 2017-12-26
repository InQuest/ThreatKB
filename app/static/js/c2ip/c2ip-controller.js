'use strict';

angular.module('ThreatKB')
    .controller('C2ipController', ['$scope', '$filter', '$http', '$uibModal', 'resolvedC2ip', 'C2ip', 'Cfg_states', 'growl', 'Users', 'openModalForId', 'uiGridConstants',
        function ($scope, $filter, $http, $uibModal, resolvedC2ip, C2ip, Cfg_states, growl, Users, openModalForId, uiGridConstants) {

            $scope.c2ips = resolvedC2ip;

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
                            if (column.filters[0].term !== undefined && column.filters[0].term !== null) {
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
                },
                rowHeight: 35,
                columnDefs:
                    [
                        {field: 'ip', displayName: 'IP'},
                        {field: 'asn', displayName: 'ASN', enableSorting: false},
                        {field: 'country', enableSorting: false},
                        {
                            field: 'state',
                            displayName: 'State',
                            enableSorting: false,
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
                });
            };

            getPage();

            if (openModalForId !== null) {
                $scope.update(openModalForId);
            }
        }])
    .controller('C2ipSaveController', ['$scope', '$http', '$uibModalInstance', '$location', 'c2ip', 'metadata', 'Comments', 'Cfg_states', 'Tags', 'growl', 'Bookmarks',
        function ($scope, $http, $uibModalInstance, $location, c2ip, metadata, Comments, Cfg_states, Tags, growl, Bookmarks) {
            $scope.c2ip = c2ip;
            $scope.c2ip.new_comment = "";
            $scope.Comments = Comments;
            $scope.metadata = metadata;

            $scope.update_selected_metadata = function (m, selected) {
                c2ip.metadata_values[m.key].value = selected;
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
                return $location.absUrl() + "/" + id;
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
