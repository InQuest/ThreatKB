'use strict';

angular.module('ThreatKB')
    .controller('C2dnsController', ['$scope', '$timeout', '$filter', '$q', '$http', '$uibModal', 'resolvedC2dns', 'C2dns', 'Cfg_states', 'growl', 'Users', 'openModalForId', 'uiGridConstants', 'Cfg_settings', '$routeParams',
        function ($scope, $timeout, $filter, $q, $http, $uibModal, resolvedC2dns, C2dns, Cfg_states, growl, Users, openModalForId, uiGridConstants, Cfg_settings, $routeParams) {

            $scope.c2dns = resolvedC2dns;

            $scope.users = Users.query();

            $scope.cfg_states = Cfg_states.query();

            $scope.start_filter_requests_length = Cfg_settings.get({key: "START_FILTER_REQUESTS_LENGTH"});

            $('input[type=number]').on('mousewheel', function () {
                var el = $(this);
                el.blur();
                setTimeout(function () {
                    el.focus();
                }, 10);
            });

            $scope.clear_checked = function () {
                $scope.checked_indexes = [];
                $scope.checked_counter = 0;
                $scope.all_checked = false;
            };

            $scope.clear_checked();

            $scope.searches = {};
            if ($routeParams.searches) {
                $scope.searches = JSON.parse($routeParams.searches);
            }

            $scope.filterOptions = {
                filterText: ''
            };

            $scope.disable_multi_actions = function () {
                return $scope.checked_counter < 1;
            };
            $scope.get_index_from_row = function (row) {
                for (var i = 0; i < row.grid.rows.length; i++) {
                    if (row.uid === row.grid.rows[i].uid) {
                        return i;
                    }
                }
            };

            $scope.toggle_checked = function () {
                if ($scope.all_checked) {
                    $scope.check_all();
                } else {
                    $scope.uncheck_all();
                }
            };

            $scope.update_checked_counter = function (row) {
                var index = $scope.get_index_from_row(row);
                if ($scope.checked_indexes[index]) {
                    $scope.checked_counter += 1;
                } else {
                    $scope.checked_counter -= 1;
                }
            };

            $scope.uncheck_all = function () {
                for (var i = 0; i < $scope.checked_indexes.length; i++) {
                    $scope.checked_indexes[i] = false;
                }
                $scope.checked_counter = 0;
            };

            $scope.check_all = function () {
                for (var i = 0; i < $scope.checked_indexes.length; i++) {
                    $scope.checked_indexes[i] = true;
                }
                $scope.checked_counter = $scope.checked_indexes.length;
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

                            if (column.filters[0].term !== undefined && column.filters[0].term !== null
                                && ("~" === column.filters[0].term
                                    || column.filters[0].term.length >= parseInt($scope.start_filter_requests_length.value))) {
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
                            field: 'checked',
                            displayName: "",
                            width: '40',
                            enableSorting: false,
                            headerCellTemplate: '<BR><center><input style="vertical-align: middle;" type="checkbox" ng-model="grid.appScope.all_checked" ng-click="grid.appScope.toggle_checked()" /></center>',
                            cellTemplate: '<center><input type="checkbox" ng-model="grid.appScope.checked_indexes[grid.appScope.get_index_from_row(row)]" ng-change="grid.appScope.update_checked_counter(row)" /></center>'
                        },
                        {
                            field: 'domain_name',
                            width: '300'
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
                            width: '160',
                            enableFiltering: false,
                            enableColumnMenu: false,
                            enableSorting: false,
                            cellTemplate: '<div style="text-align: center;">'
                                + '<button type="button" ng-if="!row.entity.active" ng-click="grid.appScope.activateArtifact(row.entity.id, row.entity.domain_name)"'
                                + ' class="btn btn-sm">'
                                + '<small><span class="glyphicon glyphicon-check"></span>'
                                + '</small>'
                                + '</button>'
                                + '&nbsp;'
                                + '<button type="button" ng-click="grid.appScope.viewDns(row.entity.id)"'
                                + ' class="btn btn-sm">'
                                + '<small><span class="glyphicon glyphicon-eye-open"></span>'
                                + '</small>'
                                + '</button>'
                                + '&nbsp;'
                                + '<button type="button" ng-click="grid.appScope.update(row.entity.id)"'
                                + ' class="btn btn-sm">'
                                + '<small><span class="glyphicon glyphicon-pencil"></span>'
                                + '</small>'
                                + '</button>'
                                + '&nbsp;'
                                + '<button ng-if="row.entity.active" confirmed-click="grid.appScope.delete(row.entity.id)"'
                                + ' ng-confirm-click="Are you sure you want to '
                                + 'deactivate this c2dns?" class="btn btn-sm btn-danger">'
                                + '<small>'
                                + '<span class="glyphicon glyphicon-remove-circle"></span>'
                                + '</small>'
                                + '</button>'
                                + '<button ng-if="!row.entity.active" confirmed-click="grid.appScope.delete(row.entity.id)"'
                                + ' ng-confirm-click="Are you sure you want to '
                                + 'delete this c2dns permanently?" class="btn btn-sm btn-danger">'
                                + '<small>'
                                + '<span class="glyphicon glyphicon-remove-circle"></span>'
                                + '</small>'
                                + '</button>'
                                + '</div>'
                        }
                    ]
            };

            // Debounce getPage requests (by 1000ms)
            var cancelGetPage = null,
                getPageDelay = 1000;
            var getPage = _.debounce(
                function () {
                    // Cancel previous request (if any found)
                    if (cancelGetPage) {
                        cancelGetPage.resolve();
                    }
                    // Compose request
                    var url = '/ThreatKB/c2dns?';
                    url += 'page_number=' + (paginationOptions.pageNumber - 1);
                    url += '&page_size=' + paginationOptions.pageSize;
                    url += '&view=' + $scope.view_selected;

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
                    // Set new request cancelation trigger
                    cancelGetPage = $q.defer();
                    // ... and fire off a cancelable request
                    $http.get(url, { timeout: cancelGetPage.promise })
                    $http.get(url)
                        .then(function (response) {
                            $scope.gridOptions.totalItems = response.data.total_count;
                            $scope.gridOptions.data = response.data.data;
                            $scope.c2dns = $scope.gridOptions.data;
                            $scope.clear_checked();
                            for (var i = 0; i < $scope.gridOptions.data.length; i++) {
                                $scope.checked_indexes.push(false);
                            }
                            $scope.gridApi.grid.gridHeight = parseInt($scope.getTableHeight().height);  // Re-apply table height calculation, based on new data
                            $scope.gridApi.core.refresh();
                        }, function (error) {
                        });
                },
                getPageDelay
            );


            $scope.getPage = getPage;

            $scope.view_options = ["Active Only", "All", "Inactive Only"];
            $scope.view_selected = "Active Only";
            $scope.change_view = function (item, model) {
                $scope.view_selected = item;

                $scope.getPage();
            };

            getPage();

            $scope.getTableHeight = function () {
                var rowHeight = $scope.gridOptions.rowHeight;
                var headerHeight = 100;
                return {
                    height: ($scope.gridOptions.data.length * rowHeight + headerHeight) + "px"
                };
            };

            $scope.create = function () {
                $scope.clear();
                $scope.edit();
            };

            $scope.update = function (id) {
                $scope.c2dns = C2dns.resource.get({id: id});
                $scope.cfg_states = Cfg_states.query();
                $scope.users = Users.query();
                $scope.edit(id);
            };

            $scope.viewDns = function (id) {
                $scope.c2dns = C2dns.resource.get({id: id});
                $scope.view(id);
            };

            $scope.delete = function (id) {
                C2dns.resource.delete({id: id}, function () {
                    getPage();
                });
            };

            $scope.delete_all_inactive = function () {
                C2dns.delete_all_inactive().then(function (success) {
                    growl.info("Successfully deleted all inactive DNS", {ttl: 3000});
                    getPage();
                })
            };

            $scope.activateArtifact = function (id, name) {
                C2dns.activateArtifact(id).then(function (success) {
                    growl.info("Successfully activated signature " + name, {ttl: 3000});
                    getPage();
                });
            };

            $scope.save_batch = function () {
                var c2dnsToUpdate = {
                    owner_user: $scope.batch.owner,
                    state: $scope.batch.state,
                    description: $scope.batch.description,
                    tags: $scope.batch.tags,
                    ids: []
                };
                for (var i = 0; i < $scope.checked_indexes.length; i++) {
                    if ($scope.checked_indexes[i]) {
                        c2dnsToUpdate.ids.push($scope.c2dns[i].id);
                    }
                }
                C2dns.updateBatch(c2dnsToUpdate).then(function (response) {
                    getPage();
                }, function (error) {
                    growl.error(error.data, {ttl: -1});
                });
            };

            $scope.save = function (id_or_dns) {
                var id = id_or_dns;
                if (typeof (id_or_dns) === "object") {
                    id = id_or_dns.id;
                    $scope.c2dns = id_or_dns;
                }

                if (id) {
                    C2dns.resource.update({id: id}, $scope.c2dns, function () {
                        getPage();
                    }, function (error) {
                        growl.error(error.data, {ttl: -1});
                        $scope.openDnsModal(id);
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
                            if (typeof (entity.default) == "object") {
                                $scope.c2dns.metadata_values[entity.key] = {value: entity.default.choice};
                            } else {
                                $scope.c2dns.metadata_values[entity.key] = {value: entity.default};
                            }
                        }
                    }

                    C2dns.resource.save($scope.c2dns, function () {
                        getPage();
                    }, function (error) {
                        growl.error(error.data, {ttl: -1});
                        $scope.openDnsModal(id);
                    });
                }
            };

            $scope.clear_batch = function () {
                $scope.batch = {
                    owner: null,
                    state: null,
                    description: null,
                    tags: null
                };
            };

            $scope.clear = function () {
                $scope.checked_indexes = [];
                $scope.c2dns = {
                    "date_created": "",
                    "date_modified": "",
                    "state": "",
                    "domain_name": "",
                    "match_type": "",
                    "reference_link": "",
                    "expiration_timestamp": "",
                    "description": "",
                    "id": "",
                    "tags": []
                };
            };

            $scope.openDnsModal = function (id) {
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
                }, function () {
                    getPage();
                });
            };

            $scope.clear_batch();
            $scope.open_batch = function () {
                $scope.clear_batch();
                $scope.batch_edit();
            };
            $scope.batch_delete = function () {
                var c2dnsToDelete = {
                    ids: []
                };
                for (var i = 0; i < $scope.checked_indexes.length; i++) {
                    if ($scope.checked_indexes[i]) {
                        c2dnsToDelete.ids.push($scope.c2dns[i].id);
                    }
                }
                C2dns.deleteBatch(c2dnsToDelete).then(function (response) {
                    getPage();
                }, function (error) {
                    growl.error(error.data, {ttl: -1});
                });
            };
            $scope.batch_edit = function () {
                var be = $uibModal.open({
                    templateUrl: 'c2dns-batch_edit.html',
                    controller: 'C2dnsBatchEditController',
                    size: 'lg',
                    backdrop: 'static',
                    resolve: {
                        batch: function () {
                            return $scope.batch;
                        }
                    }
                });

                be.result.then(function (batch) {
                    $scope.batch = batch;
                    $scope.save_batch();
                }, function () {
                    getPage();
                });
            };
            $scope.edit = function (id) {
                $scope.openDnsModal(id);
            };

            $scope.view = function (id) {
                var dns_view = $uibModal.open({
                    templateUrl: 'c2dns-view.html',
                    controller: 'C2dnsViewController',
                    size: 'lg',
                    backdrop: 'static',
                    resolve: {
                        c2dns: function () {
                            return $scope.c2dns;
                        }
                    }
                });
            };

            if (openModalForId !== null) {
                if (openModalForId === "add") {
                    $scope.create();
                } else {
                    $scope.update(openModalForId);
                }
            }
        }])
    .controller('C2dnsSaveController', ['$scope', '$http', '$uibModalInstance', '$location', '$window', 'C2dns', 'c2dns', 'metadata', 'Cfg_states', 'Comments', 'Tags', 'growl', 'Bookmarks', 'hotkeys', 'Users',
        function ($scope, $http, $uibModalInstance, $location, $window, C2dns, c2dns, metadata, Cfg_states, Comments, Tags, growl, Bookmarks, hotkeys, Users) {

            if (c2dns.$promise !== undefined && c2dns.$promise !== null) {
                c2dns.$promise.then(
                    function (c2) {
                        $window.document.title = "ThreatKB: " + c2.domain_name;
                    }
                );
            }

            $scope.c2dns = c2dns;
            $scope.c2dns.new_comment = "";
            $scope.Comments = Comments;
            $scope.metadata = metadata;
            if (!$scope.c2dns.id) {
                $scope.c2dns.metadata = metadata;
            }

            $scope.users = Users.query();

            $scope.save_artifact = function () {
                C2dns.resource.update({id: $scope.c2dns.id}, $scope.c2dns,
                    function (data) {
                        if (!data) {
                            growl.error(error, {ttl: -1});
                        } else {
                            growl.info("Successfully saved dns artifact '" + $scope.c2dns.domain_name + "'.", {ttl: 2000});
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
                var location = $location.absUrl();
                var last_spot = location.split("/")[location.split("/").length - 1]
                if (isNaN(parseInt(last_spot, 10))) {
                    return $location.absUrl() + "/" + id;
                } else if (!isNaN(parseInt(last_spot, 10)) && last_spot != id) {
                    return $location.absUrl().replace(/\/[0-9]+$/, "/" + id)
                }
                return $location.absUrl();
            };

            $scope.match_types = ['exact', 'wildcard'];
            if (!$scope.c2dns.match_type) {
                $scope.c2dns.match_type = $scope.match_types[0];
            }

            $scope.dateOptions = {
                showWeeks: false,
            };

            $scope.openDatepicker = function() {
                $scope.expiration_timestamp.opened = true;
            };

            $scope.expiration_timestamp = {
                opened: false
            };

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
                    });
                });
            };

            $scope.delete_comment = function (id, comment_id) {
                $scope.Comments.resource.delete({id: comment_id}, function () {
                    $scope.c2dns.comments = $scope.Comments.resource.query({
                        entity_type: Comments.ENTITY_MAPPING.DNS,
                        entity_id: id
                    });
                });
            };

            $scope.ok = function () {
                // Check if outstanding comment
                if ($scope.c2dns.new_comment && $scope.c2dns.new_comment.trim() && confirm('There is a unsaved comment, do you wish to save it as well?')) {
                    $scope.add_comment($scope.c2dns.id);
                }
                // Close modal
                $window.document.title = "ThreatKB";
                $uibModalInstance.close($scope.c2dns);
            };

            $scope.cancel = function () {
                // Check if outstanding comment
                if ($scope.c2dns.new_comment && $scope.c2dns.new_comment.trim() && confirm('There is a unsaved comment, do you wish to save it?')) {
                    $scope.add_comment($scope.c2dns.id);
                }
                // Close modal
                $window.document.title = "ThreatKB";
                $uibModalInstance.dismiss('cancel');
            };

            $scope.loadTags = function (query) {
                return Tags.loadTags(query);
            };
        }])
    .controller('C2dnsViewController', ['$scope', '$uibModalInstance', 'c2dns', '$location', '$window', 'Cfg_settings',
        function ($scope, $uibModalInstance, c2dns, $location, $window, Cfg_settings) {

            $scope.static_references = {};
            Cfg_settings.get({key: "ARTIFACT_STATIC_REFERENCES"}).$promise.then(function (staticReferences) {
                    $scope.static_references = JSON.parse(staticReferences.value);
                }
            );

            c2dns.$promise.then(
                function (c2) {
                    $window.document.title = "ThreatKB: " + c2.domain_name;
                }
            );

            $scope.c2dns = c2dns;

            $scope.edit = function (id) {
                var location = $location.absUrl();
                var last_spot = location.split("/")[location.split("/").length - 1];
                $uibModalInstance.close($scope.c2dns);
                if (isNaN(parseInt(last_spot, 10))) {
                    $window.location.href = $location.absUrl() + "/" + id;
                    return;
                } else if (!isNaN(parseInt(last_spot, 10)) && last_spot !== id) {
                    $window.location.href = $location.absUrl().replace(/\/[0-9]+$/, "/" + id);
                    return;
                }
                $window.location.href = $location.absUrl();
            };

            $scope.ok = function () {
                $uibModalInstance.close($scope.c2dns);
            };

            $scope.cancel = function () {
                $uibModalInstance.dismiss('cancel');
            };

        }])
    .controller('C2dnsBatchEditController', ['$scope', '$uibModalInstance', 'batch', 'Users', 'Cfg_states', 'Tags',
        function ($scope, $uibModalInstance, batch, Users, Cfg_states, Tags) {
            $scope.batch = batch;

            $scope.users = Users.query();

            $scope.cfg_states = Cfg_states.query();

            $scope.ok = function () {
                $uibModalInstance.close($scope.batch);
            };

            $scope.cancel = function () {
                $uibModalInstance.dismiss('cancel');
            };

            $scope.loadTags = function (query) {
                return Tags.loadTags(query);
            };
        }]);
