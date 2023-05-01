'use strict';

angular.module('ThreatKB')
    .controller('Yara_ruleController', ['$scope', '$timeout', '$filter', '$q', '$http', '$uibModal', 'Yara_rule', 'Cfg_states', 'CfgCategoryRangeMapping', 'Users', 'growl', 'openModalForId', 'uiGridConstants', 'FileSaver', 'Blob', 'Cfg_settings', '$routeParams', 'blockUI',
        function ($scope, $timeout, $filter, $q, $http, $uibModal, Yara_rule, Cfg_states, CfgCategoryRangeMapping, Users, growl, openModalForId, uiGridConstants, FileSaver, Blob, Cfg_settings, $routeParams, blockUI) {

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
                $scope.copy_rules();
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
                $scope.copy_rules();
            };

            var c = new ClipboardJS('#batchCopyBtn', {
                text: function (trigger) {
                    return trigger.getAttribute('aria-label');
                }
            });
            $scope.get_sigs_to_copy = function () {
                var sigsToCopy = {
                    ids: []
                };
                for (var i = 0; i < $scope.checked_indexes.length; i++) {
                    if ($scope.checked_indexes[i]) {
                        sigsToCopy.ids.push($scope.yara_rules[i].id);
                    }
                }
                return sigsToCopy;
            };
            $scope.copy_rules = function () {
                blockUI.start("");
                Yara_rule.copySignatures($scope.get_sigs_to_copy()).then(function (response) {
                    blockUI.stop();
                    document.getElementById('batchCopyBtn').setAttribute("aria-label", response);
                }, function (error) {
                });
            };

            $scope.download_rules = function () {
                Yara_rule.copySignatures($scope.get_sigs_to_copy()).then(function (response) {
                    try {
                        FileSaver.saveAs(new Blob([response], {type: "text/plain"}), "yara_rules.txt");
                    } catch (error) {
                        growl.error("Error downloading signatures.", {ttl: -1});
                    }
                }, function (error) {
                    growl.error(error.data, {ttl: -1});
                });

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
                            field: 'checked',
                            displayName: "",
                            width: '40',
                            enableSorting: false,
                            headerCellTemplate: '<BR><center><input style="vertical-align: middle;" type="checkbox" ng-model="grid.appScope.all_checked" ng-click="grid.appScope.toggle_checked()" /></center>',
                            cellTemplate: '<center><input type="checkbox" ng-model="grid.appScope.checked_indexes[grid.appScope.get_index_from_row(row)]" ng-change="grid.appScope.update_checked_counter(row)" /></center>'
                        },
                        {
                            field: 'eventid',
                            displayName: "Event ID",
                            width: '120',
                            enableCellEditOnFocus: true
                        },
                        {
                            field: 'name',
                            enableSorting: true
                        },
                        {
                            field: 'creation_date',
                            displayName: "Created Date",
                            enableSorting: true,
                            width: '150',
                            cellFilter: 'date:\'yyyy-MM-dd HH:mm:ss\''
                        },
                        {
                            field: 'last_revision_date',
                            displayName: "Revision Date",
                            enableSorting: true,
                            width: '150',
                            cellFilter: 'date:\'yyyy-MM-dd HH:mm:ss\''
                        },
                        {
                            field: 'category',
                            width: '110',
                            enableSorting: true
                        },
                        {
                            field: 'state',
                            displayName: 'State',
                            width: '110',
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
                            width: '180',
                            enableFiltering: false,
                            enableColumnMenu: false,
                            enableSorting: false,
                            cellTemplate: '<div style="text-align: center;">'
                                + '<button type="button" ng-if="!row.entity.active" ng-click="grid.appScope.activateRule(row.entity.id, row.entity.name)"'
                                + ' class="btn btn-sm">'
                                + '<small><span class="glyphicon glyphicon-check"></span>'
                                + '</small>'
                                + '</button>'
                                + '&nbsp;'
                                + '<button type="button" ng-click="grid.appScope.viewRule(row.entity.id)"'
                                + ' class="btn btn-sm">'
                                + '<small><span class="glyphicon glyphicon-eye-open"></span>'
                                + '</small>'
                                + '</button>'
                                + '&nbsp;'
                                + '<button type="button" ng-click="grid.appScope.viewRevision(row.entity.id)"'
                                + ' class="btn btn-sm">'
                                + '<small><span class="glyphicon glyphicon-list-alt"></span>'
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
                                + 'deactivate this signature?" class="btn btn-sm btn-danger">'
                                + '<small>'
                                + '<span class="glyphicon glyphicon-remove-circle"></span>'
                                + '</small>'
                                + '</button>'
                                + '<button ng-if="!row.entity.active" confirmed-click="grid.appScope.delete(row.entity.id)"'
                                + ' ng-confirm-click="Are you sure you want to '
                                + 'delete this signature?" class="btn btn-sm btn-danger">'
                                + '<small>'
                                + '<span class="glyphicon glyphicon-remove-circle"></span>'
                                + '</small>'
                                + '</button>'
                                + '</div>'
                        }
                    ]
            };

            $scope.state = {};

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
                    var url = '/ThreatKB/yara_rules?';
                    url += 'page_number=' + (paginationOptions.pageNumber - 1);
                    url += '&page_size=' + paginationOptions.pageSize;
                    url += '&include_yara_string=0';
                    url += '&short=1';
                    url += '&include_metadata=0';
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
                        .then(function (response) {
                            $scope.gridOptions.totalItems = response.data.total_count;
                            $scope.gridOptions.data = response.data.data;
                            $scope.yara_rules = $scope.gridOptions.data;
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

            $scope.delete_all_inactive = function () {
                Yara_rule.delete_all_inactive().then(function (success) {
                    growl.info("Successfully deleted all inactive yara rules", {ttl: 3000});
                    getPage();
                })
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
                $scope.yara_rule = Yara_rule.resource.get({id: id, include_yara_string: 1, include_revisions: 0});
                $scope.cfg_states = Cfg_states.query();
                $scope.users = Users.query();
                $scope.cfg_category_range_mapping = CfgCategoryRangeMapping.query();
                $scope.edit(id);
            };

            $scope.viewRule = function (id) {
                $scope.yara_rule = Yara_rule.resource.get({id: id, include_yara_string: 1, include_revisions: 0});
                $scope.view(id);
            };

            $scope.viewRevision = function (id) {
                $scope.yara_rule = Yara_rule.resource.get({id: id, include_yara_string: 1, include_revisions: 1});
                $scope.revision_view(id);
            };

            $scope.activateRule = function (id, name) {
                Yara_rule.activateRule(id).then(function (success) {
                    growl.info("Successfully activated signature " + name, {ttl: 3000});
                    getPage();
                });
            };

            $scope.delete = function (id) {
                Yara_rule.resource.delete({id: id}, function () {
                    getPage();
                });
            };

            $scope.save_batch = function () {
                var sigsToUpdate = {
                    owner_user: $scope.batch.owner,
                    state: $scope.batch.state,
                    description: $scope.batch.description,
                    category: $scope.batch.category,
                    tags: $scope.batch.tags,
                    ids: []
                };
                for (var i = 0; i < $scope.checked_indexes.length; i++) {
                    if ($scope.checked_indexes[i]) {
                        sigsToUpdate.ids.push($scope.yara_rules[i].id);
                    }
                }
                Yara_rule.updateBatch(sigsToUpdate).then(function (response) {
                    getPage();
                }, function (error) {
                    growl.error(error.data, {ttl: -1});
                });
            };

            $scope.save = function (id_or_rule) {
                var id = id_or_rule;
                if (typeof (id_or_rule) === "object") {
                    if (id_or_rule.merge) {
                        Yara_rule.merge_signature_by_id($scope.yara_rule.id, id_or_rule.id).then(function (data) {
                            growl.info("Successfully merged '" + $scope.yara_rule.name + "' into '" + id_or_rule.name + "'", {ttl: 3000});
                        }, function (error) {
                            growl.error(error, {ttl: -1})
                        })
                    } else {
                        id = id_or_rule.id;
                        $scope.yara_rule = id_or_rule;
                    }
                }

                if (parseInt(id)) {
                    Yara_rule.resource.update({id: id}, $scope.yara_rule, function () {
                        growl.info("Successfully saved signature '" + $scope.yara_rule.name + "'.", {ttl: 2000});
                        getPage();
                    }, function (err) {
                        growl.error(err.data);
                        $scope.openYaraModal(id);
                    });
                } else {
                    $scope.yara_rule.metadata_values = {};

                    if ($scope.yara_rule.metadata[0].hasOwnProperty("string")) {
                        for (var i = 0; i < $scope.yara_rule.metadata[0].string.length; i++) {
                            var entity = $scope.yara_rule.metadata[0].string[i];
                            $scope.yara_rule.metadata_values[entity.key] = {value: entity.default};
                        }
                    }
                    if ($scope.yara_rule.metadata[0].hasOwnProperty("multiline_comment")) {
                        for (var i = 0; i < $scope.yara_rule.metadata[0].multiline_comment.length; i++) {
                            var entity = $scope.yara_rule.metadata[0].multiline_comment[i];
                            $scope.yara_rule.metadata_values[entity.key] = {value: entity.default};
                        }
                    }

                    if ($scope.yara_rule.metadata[0].hasOwnProperty("date")) {
                        for (var i = 0; i < $scope.yara_rule.metadata[0].date.length; i++) {
                            var entity = $scope.yara_rule.metadata[0].date[i];
                            $scope.yara_rule.metadata_values[entity.key] = {value: entity.default};
                        }
                    }

                    if ($scope.yara_rule.metadata[0].hasOwnProperty("integer")) {
                        for (var i = 0; i < $scope.yara_rule.metadata[0].integer.length; i++) {
                            var entity = $scope.yara_rule.metadata[0].integer[i];
                            $scope.yara_rule.metadata_values[entity.key] = {value: entity.default};
                        }
                    }

                    if ($scope.yara_rule.metadata[0].hasOwnProperty("select")) {
                        for (var i = 0; i < $scope.yara_rule.metadata[0].select.length; i++) {
                            var entity = $scope.yara_rule.metadata[0].select[i];
                            if (typeof (entity.default) == "object") {
                                $scope.yara_rule.metadata_values[entity.key] = {value: entity.default.choice};
                            } else {
                                $scope.yara_rule.metadata_values[entity.key] = {value: entity.default};
                            }
                        }
                    }

                    Yara_rule.resource.save($scope.yara_rule, function () {
                        getPage();
                    }, function (err) {
                        growl.error(err.data);
                        $scope.openYaraModal(id);
                    });
                }
            };

            $scope.clear_batch = function () {
                $scope.batch = {
                    owner: null,
                    state: null,
                    description: null,
                    category: null,
                    tags: null
                };
            };

            $scope.clear = function () {
                $scope.checked_indexes = [];
                $scope.yara_rule = {
                    "creation_date": "",
                    "last_revision_date": "",
                    "state": "",
                    "name": "",
                    "category": "",
                    "condition": "",
                    "strings": "",
                    "eventid": "",
                    "id": "",
                    "tags": [],
                    "comments": [],
                    "files": [],
                    "imports": ""
                };
            };

            $scope.openYaraModal = function (id) {
                var yara_ruleSave = $uibModal.open({
                    templateUrl: 'yara_rule-save.html',
                    controller: 'Yara_ruleSaveController',
                    size: 'lg',
                    backdrop: 'static',
                    resolve: {
                        yara_rule: function () {
                            return $scope.yara_rule;
                        },
                        yara_rules: function () {
                            return $scope.yara_rules;
                        },
                        metadata: ['Metadata', function (Metadata) {
                            return Metadata.query({
                                filter: "signature",
                                format: "dict"
                            });
                        }]
                    }
                });

                yara_ruleSave.result.then(function (entity) {
                    if (entity.merge) {
                        $scope.save(entity);
                    } else {
                        $scope.yara_rule = entity;
                        $scope.save(id);
                    }
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
                var sigsToDelete = {
                    ids: []
                };
                for (var i = 0; i < $scope.checked_indexes.length; i++) {
                    if ($scope.checked_indexes[i]) {
                        sigsToDelete.ids.push($scope.yara_rules[i].id);
                    }
                }
                Yara_rule.deleteBatch(sigsToDelete).then(function (response) {
                    getPage();
                }, function (error) {
                    growl.error(error.data, {ttl: -1});
                });
            };

            $scope.batch_edit = function () {
                var be = $uibModal.open({
                    templateUrl: 'yara_rule-batch_edit.html',
                    controller: 'Yara_ruleBatchEditController',
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
                $scope.openYaraModal(id);
            };


            $scope.merge_signatures = function () {
                var sigsToMerge = [];
                for (var i = 0; i < $scope.checked_indexes.length; i++) {
                    if ($scope.checked_indexes[i]) {
                        sigsToMerge.push($scope.yara_rules[i].id);
                    }
                }
                Yara_rule.merge_signatures(sigsToMerge).then(function (response) {
                    $scope.update(response.id)
                }, function (error) {
                    growl.error(error, {ttl: -1});
                });
            };

            $scope.view = function (id) {
                var yara_view = $uibModal.open({
                    templateUrl: 'yara_rule-view.html',
                    controller: 'Yara_ruleViewController',
                    size: 'lg',
                    backdrop: 'static',
                    resolve: {
                        yara_rule: function () {
                            return $scope.yara_rule;
                        }
                    }
                });
            };

            $scope.revision_view = function (id) {
                const revision_view = $uibModal.open({
                    templateUrl: 'yara_rule-revision.html',
                    controller: 'Yara_ruleRevisionViewController',
                    size: 'lg',
                    backdrop: 'static',
                    resolve: {
                        yara_rule: function () {
                            return $scope.yara_rule;
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

            $scope.revisionIsOpen = false;

        }])
    .controller('Yara_ruleSaveController', ['$scope', '$http', '$cookies', '$uibModal', '$uibModalInstance', '$location', '$window', 'yara_rule', 'yara_rules', 'metadata', 'Cfg_states', 'Comments', 'Upload', 'Files', 'CfgCategoryRangeMapping', 'growl', 'Users', 'Tags', 'Yara_rule', 'Cfg_settings', 'Bookmarks', 'hotkeys',
        function ($scope, $http, $cookies, $uibModal, $uibModalInstance, $location, $window, yara_rule, yara_rules, metadata, Cfg_states, Comments, Upload, Files, CfgCategoryRangeMapping, growl, Users, Tags, Yara_rule, Cfg_settings, Bookmarks, hotkeys) {

            if (yara_rule.$promise !== null && yara_rule.$promise !== undefined) {
                yara_rule.$promise.then(
                    function (yr) {
                        $window.document.title = "ThreatKB: " + yr.name;
                    }
                );
            }


            var mitre_techniques = Cfg_settings.get({key: "MITRE_TECHNIQUES"});
            if (mitre_techniques.$promise !== null && mitre_techniques.$promise !== undefined) {
                mitre_techniques.$promise.then(
                    function (techniques) {
                        $scope.mitre_techniques = techniques.value.split(",");
                    }
                );
            }

            var mitre_sub_techniques = Cfg_settings.get({key: "MITRE_SUB_TECHNIQUES"});
            if (mitre_sub_techniques.$promise !== null && mitre_sub_techniques.$promise !== undefined) {
                mitre_sub_techniques.$promise.then(
                    function (subtechniques) {
                        $scope.mitre_sub_techniques = subtechniques.value.split(",");
                    }
                );
            }

            var mitre_tactics = Cfg_settings.get({key: "MITRE_TACTICS"});
            if (mitre_tactics.$promise !== null && mitre_tactics.$promise !== undefined) {
                mitre_tactics.$promise.then(
                    function (tactics) {
                        $scope.mitre_tactics = tactics.value.split(",");
                    }
                );
            }

            $scope.yara_rule = yara_rule;
            $scope.yara_rules = yara_rules;
            $scope.metadata = metadata;
            $scope.yara_rule.new_comment = "";
            $scope.Comments = Comments;
            $scope.Files = Files;
            $scope.selected_signature = null;

            $scope.selectedRevisions = {
                main: null,
                compared: null
            };
            $scope.selected_revision = null;
            $scope.compared_revision = null;

            $scope.users = Users.query();

            $scope.editor = {
                wrap: ($cookies.get("wrap_editor") === "true")
            };

            if ($scope.editor.wrap == null) {
                $scope.editor.wrap = false;
                var expireDate = new Date();
                expireDate.setDate(expireDate.getDate() + 365);
                $cookies.put("wrap_editor", $scope.editor.wrap, {expires: expireDate});
            }

            $scope.change_wrap_editor = function () {
                var expireDate = new Date();
                expireDate.setDate(expireDate.getDate() + 365);
                $cookies.put("wrap_editor", $scope.editor.wrap, {expires: expireDate});
            };

            $scope.save_artifact = function () {

                Yara_rule.resource.update({id: $scope.yara_rule.id}, $scope.yara_rule,
                    function (data) {
                        if (!data) {
                            growl.error(error.data, {ttl: -1});
                        } else {
                            $scope.yara_rule.state = data.state;
                            growl.info("Successfully saved signature '" + $scope.yara_rule.name + "'.", {ttl: 2000});
                        }
                    },
                    function (error) {
                        growl.error(error.data, {ttl: -1});
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
            }).add({
                combo: 'ctrl+w',
                description: 'Toggle word wrap',
                allowIn: ['INPUT', 'SELECT', 'TEXTAREA'],
                callback: function () {
                    $scope.editor.wrap = !$scope.editor.wrap;
                    $scope.change_wrap_editor();
                }
            });

            if (!$scope.yara_rule.id) {
                $scope.yara_rule.metadata = metadata;
            }


            $scope.update_selected_metadata = function (m, selected) {
                if (!$scope.yara_rule.metadata_values[m.key]) {
                    $scope.yara_rule.metadata_values[m.key] = {};
                }
                $scope.yara_rule.metadata_values[m.key].value = selected.choice;
            };


            $scope.file_store_path = Cfg_settings.get({key: "FILE_STORE_PATH"});
            $scope.entity_mapping = Comments.ENTITY_MAPPING;

            if ($scope.yara_rule.$promise !== undefined) {
                $scope.yara_rule.$promise.then(function (result) {
                }, function (errorMsg) {
                    growl.error("Yara Rule Not Found", {ttl: -1});
                    $uibModalInstance.dismiss('cancel');
                });
            }

            $scope.update_selected_metadata = function (m, selected) {
                yara_rule.metadata_values[m.key].value = selected.choice;
            };

            $scope.bookmark = function (id) {
                Bookmarks.createBookmark(Bookmarks.ENTITY_MAPPING.SIGNATURE, id).then(function (data) {
                    $scope.yara_rule.bookmarked = true;
                });
            };

            $scope.unbookmark = function (id) {
                Bookmarks.deleteBookmark(Bookmarks.ENTITY_MAPPING.SIGNATURE, id).then(function (data) {
                    $scope.yara_rule.bookmarked = false;
                });
            };

            $scope.getPermalink = function (id) {
                var location = $location.absUrl();
                var last_spot = location.split("/")[location.split("/").length - 1];
                if (isNaN(parseInt(last_spot, 10))) {
                    return $location.absUrl() + "/" + id;
                } else if (!isNaN(parseInt(last_spot, 10)) && last_spot !== id) {
                    return $location.absUrl().replace(/\/[0-9]+$/, "/" + id)
                }
                return $location.absUrl();
            };

            $scope.dateOptions = {
                showWeeks: false,
            };

            $scope.datepickers = {};
            $scope.openDatepicker = function(id) {
                $scope.datepickers[id] = true;
            };

            $scope.cfg_states = Cfg_states.query();
            $scope.cfg_category_range_mapping = CfgCategoryRangeMapping.query();
            $scope.do_not_bump_revision = true;

            $scope.just_opened = true;
            $scope.negTestDir = Cfg_settings.get({key: "NEGATIVE_TESTING_FILE_DIRECTORY"});
            $scope.testingPos = false;
            $scope.testingNeg = false;

            $scope.print_comment = function (comment) {
                return comment.comment.replace(/(?:\r\n|\r|\n)/g, "<BR>");
            };

            $scope.update_selected_signature = function (yara_rule) {
                $scope.selected_signature = yara_rule;
            };

            $scope.add_comment = function (id) {
                if (!$scope.yara_rule.new_comment) {
                    return;
                }

                $scope.Comments.resource.save({
                    comment: $scope.yara_rule.new_comment,
                    entity_type: Comments.ENTITY_MAPPING.SIGNATURE,
                    entity_id: id
                }, function () {
                    $scope.yara_rule.new_comment = "";
                    $scope.yara_rule.comments = $scope.Comments.resource.query({
                        entity_type: Comments.ENTITY_MAPPING.SIGNATURE,
                        entity_id: id
                    });
                });
            };

            $scope.closeAndViewRevision = function(id) {
                $window.document.title = "ThreatKB";
                $uibModalInstance.close($scope.yara_rule);
                $window.location.href = $location.absUrl().replace(/\/[0-9]+$/, "");
                $uibModal.open({
                    templateUrl: 'yara_rule-revision.html',
                    controller: 'Yara_ruleRevisionViewController',
                    size: 'lg',
                    backdrop: 'static',
                    resolve: {
                        yara_rule: function () {
                            return $scope.yara_rule;
                        }
                    }
                });
            }

            $scope.$watch('files', function () {
                $scope.upload($scope.files);
            });


            $scope.delete_file = function (file_id) {
                Yara_rule.deleteFile({id: file_id}).then(function (resp) {
                    growl.info("Successfully deleted file", {ttl: 3000});
                    $scope.yara_rule.files = $scope.Files.resource.query({
                        entity_type: Files.ENTITY_MAPPING.SIGNATURE,
                        entity_id: $scope.yara_rule.id
                    });
                }, function (error) {
                    console.log('Error status: ' + error.status);
                    growl.error(error);
                })
            };

            $scope.delete_file_path = function (file_id) {
                Yara_rule.deleteFilePath({id: file_id}).then(function (resp) {
                    growl.info("Successfully deleted file path", {ttl: 3000});
                    $scope.yara_rule.files = $scope.Files.resource.query({
                        entity_type: Files.ENTITY_MAPPING.SIGNATURE,
                        entity_id: $scope.yara_rule.id
                    });
                }, function (error) {
                    console.log('Error status: ' + error.status);
                    growl.error(error);
                })
            };

            $scope.upload = function (id, files) {
                if (files && files.length) {
                    for (var i = 0; i < files.length; i++) {
                        var file = files[i];
                        if (!file.$error) {
                            Upload.upload({
                                url: '/ThreatKB/file_upload',
                                method: 'POST',
                                data: {
                                    file: file,
                                    entity_type: Files.ENTITY_MAPPING.SIGNATURE,
                                    entity_id: id
                                }
                            }).then(function (resp) {
                                console.log('Success ' + resp.config.data.file.name + 'uploaded.');
                                $scope.yara_rule.files = $scope.Files.resource.query({
                                    entity_type: Files.ENTITY_MAPPING.SIGNATURE,
                                    entity_id: id
                                });
                                growl.info('Success ' + JSON.stringify(resp.data, null, 2));
                            }, function (resp) {
                                console.log('Error status: ' + resp.status);
                                growl.error(resp);
                            }, function (evt) {
                                var progressPercentage = parseInt(100.0 * evt.loaded / evt.total);
                                console.log('progress: ' + progressPercentage + '% ' + evt.config.data.file.name);
                            });
                        }
                    }
                }
            };

            $scope.ok = function () {
                // Check if outstanding comment
                if ($scope.yara_rule.new_comment && $scope.yara_rule.new_comment.trim() && confirm('There is a unsaved comment, do you wish to save it as well?')) {
                    $scope.add_comment($scope.yara_rule.id);
                }
                // Close modal
                $window.document.title = "ThreatKB";
                $uibModalInstance.close($scope.yara_rule);
            };

            $scope.cancel = function () {
                // Check if outstanding comment
                if ($scope.yara_rule.new_comment && $scope.yara_rule.new_comment.trim() && confirm('There is a unsaved comment, do you wish to save it?')) {
                    $scope.add_comment($scope.yara_rule.id);
                }
                // Close modal
                $window.document.title = "ThreatKB";
                $uibModalInstance.dismiss('cancel');
            };

            $scope.loadTags = function (query) {
                return Tags.loadTags(query);
            };

            $scope.$watch('testingPos', function () {
                $scope.testButtonTextPos = $scope.testingPos ? 'Testing...' : 'Test Signature Now';
            });

            $scope.$watch('testingNeg', function () {
                $scope.testButtonTextNeg = $scope.testingNeg ? 'Clean Testing...' : 'Clean Test Signature Now';
            });

            $scope.testSignature = function (id) {
                if (!$scope.testingPos) {
                    $scope.testingPos = true;
                    return $http.post('/ThreatKB/tests/create/' + id, {cache: false}).then(function (response) {
                        var testResponse = response.data;
                        var growlMsg = "Test Summary<br />"
                            + "---------------------<br/>"
                            + "Total Time: " + testResponse['duration'] + " ms<br/>"
                            + "Total Files: " + testResponse['files_tested'] + "<br/>"
                            + "Matches Found: " + testResponse['files_matched'] + "<br/>"
                            + "Tests Killed: " + testResponse['tests_terminated'] + "<br/>"
                            + "Errors Encountered: " + testResponse['errors_encountered'];
                        if (testResponse['errors_encountered'] > 0) {
                            growlMsg += "<br/><br/>"
                                + "Errors:<br/>"
                                + "---------------------<br/>";
                            for (var i = 0; i < testResponse['error_msgs'].length; i++) {
                                growlMsg += testResponse['error_msgs'][i] + "<br/>";
                            }
                        }
                        growl.info(growlMsg, {ttl: 5000});
                        $scope.testingPos = false;
                        return true;
                    }, function (error) {
                        growl.error(error.data, {ttl: 3000});
                        $scope.testingPos = false;
                    });
                }
            };

            $scope.negTestSignature = function (id) {
                if (!$scope.testingNeg) {
                    $scope.testingNeg = true;
                    return $http.post('/ThreatKB/tests/create/' + id + '?negative=1', {cache: false})
                        .then(function (response) {
                            var testResponse = response.data;
                            growl.info(response.data.message, {ttl: 5000});
                            $scope.testingNeg = false;
                            return true;
                        }, function (error) {
                            growl.error(error.data, {ttl: 3000});
                            $scope.testingNeg = false;
                        });
                }
            };

            $scope.merge_signature_by_id = function () {
                if (!$scope.selected_signature) {
                    return;
                }

                $scope.selected_signature.merge = true;
                $uibModalInstance.close($scope.selected_signature);
            };

        }])
    .controller('Yara_ruleViewController', ['$scope', '$uibModalInstance', 'yara_rule', '$location', '$window', '$cookies',
        function ($scope, $uibModalInstance, yara_rule, $location, $window, $cookies) {

            yara_rule.$promise.then(
                function (yr) {
                    $window.document.title = "ThreatKB: " + yr.name;
                }
            );

            $scope.editor = {
                wrap: ($cookies.get("wrap_editor") === "true")
            };

            if ($scope.editor.wrap == null) {
                $scope.editor.wrap = false;
                var expireDate = new Date();
                expireDate.setDate(expireDate.getDate() + 365);
                $cookies.put("wrap_editor", $scope.wrap_ededitor.wrapitor, {expires: expireDate});
            }

            $scope.change_wrap_editor = function () {
                var expireDate = new Date();
                expireDate.setDate(expireDate.getDate() + 365);
                $cookies.put("wrap_editor", $scope.editor.wrap, {expires: expireDate});
            };

            $scope.edit = function (id) {
                var location = $location.absUrl();
                var last_spot = location.split("/")[location.split("/").length - 1];
                $uibModalInstance.close($scope.yara_rule);
                if (isNaN(parseInt(last_spot, 10))) {
                    $window.location.href = $location.absUrl() + "/" + id;
                    return;
                } else if (!isNaN(parseInt(last_spot, 10)) && last_spot !== id) {
                    $window.location.href = $location.absUrl().replace(/\/[0-9]+$/, "/" + id);
                    return;
                }
                $window.location.href = $location.absUrl();
            };

            $scope.yara_rule = yara_rule;

            $scope.ok = function () {
                $uibModalInstance.close($scope.yara_rule);
            };

            $scope.cancel = function () {
                $uibModalInstance.dismiss('cancel');
            };

        }])
    .controller('Yara_ruleBatchEditController', ['$scope', '$uibModalInstance', 'batch', 'Users', 'Cfg_states', 'Tags', 'CfgCategoryRangeMapping',
        function ($scope, $uibModalInstance, batch, Users, Cfg_states, Tags, CfgCategoryRangeMapping) {
            $scope.batch = batch;

            $scope.users = Users.query();

            $scope.cfg_states = Cfg_states.query();

            $scope.cfg_category_range_mapping = CfgCategoryRangeMapping.query();

            $scope.ok = function () {
                $uibModalInstance.close($scope.batch);
            };

            $scope.cancel = function () {
                $uibModalInstance.dismiss('cancel');
            };

            $scope.dateOptions = {
                showWeeks: false,
            };

            $scope.datepickers = {};
            $scope.openDatepicker = function(id) {
                $scope.datepickers[id] = true;
            };

            $scope.loadTags = function (query) {
                return Tags.loadTags(query);
            };
        }])
    .controller('Yara_ruleRevisionViewController', ['$scope', '$uibModalInstance', 'yara_rule', '$location', '$window', '$cookies',
        function ($scope, $uibModalInstance, yara_rule, $location, $window, $cookies) {
            yara_rule.$promise.then(
                function (yr) {
                    $window.document.title = "ThreatKB: " + yr.name;
                }
            );

            $scope.selectedRevisions = {
                main: null,
                compared: null
            };

            $scope.edit = function (id) {
                var location = $location.absUrl();
                var last_spot = location.split("/")[location.split("/").length - 1];
                $uibModalInstance.close($scope.yara_rule);
                if (isNaN(parseInt(last_spot, 10))) {
                    $window.location.href = $location.absUrl() + "/" + id;
                    return;
                } else if (!isNaN(parseInt(last_spot, 10)) && parseInt(last_spot) !== id) {
                    $window.location.href = $location.absUrl().replace(/\/[0-9]+$/, "/" + id);
                    return;
                }
                $window.location.href = $location.absUrl();
            };

            $scope.yara_rule = yara_rule;

            $scope.ok = function () {
                $uibModalInstance.close($scope.yara_rule);
            };

            $scope.cancel = function () {
                $uibModalInstance.dismiss('cancel');
            };
        }])
    .controller('Yara_revisionController', ['$scope', 'Yara_rule',
        function ($scope, Yara_rule) {
            $scope.revision_diff = null;
            $scope.calculateRevisionDiff = function () {
                if (!$scope.selectedRevisions.compared) {
                    $scope.revision_diff = null;
                } else {
                    var dmp = new diff_match_patch(),
                        diffs = dmp.diff_main(($scope.selectedRevisions.main ? $scope.selectedRevisions.main.yara_rule_string : $scope.yara_rule.yara_rule_string), $scope.selectedRevisions.compared.yara_rule_string);
                    $scope.revision_diff = dmp.diff_prettyHtml(diffs).replace(/&para;/g, '');
                }
            };

            $scope.$watch(
                function () { return $scope.selectedRevisions.main; },
                function (value) {
                    $scope.selectedRevisions.compared = null;
                    if (value) {
                        if (!$scope.selectedRevisions.main.yara_rule_string) {
                            Yara_rule.getSignatureFromRevision($scope.selectedRevisions.main.yara_rule_id, $scope.selectedRevisions.main.revision)
                                .then(function (response) {
                                    $scope.selectedRevisions.main.yara_rule_string = response;
                                    $scope.revisionIsLoaded = true;
                                    $scope.calculateRevisionDiff();
                                }, function (error) {
                                    growl.error(error.data, {ttl: -1});
                                });
                        } else {
                            $scope.calculateRevisionDiff();
                        }
                    } else {
                        $scope.calculateRevisionDiff();
                    }
                }
            );
            $scope.$watch(
                function () { return $scope.selectedRevisions.compared; },
                function (value) {
                    if (value) {
                        if (!$scope.selectedRevisions.compared.yara_rule_string) {
                            Yara_rule.getSignatureFromRevision($scope.selectedRevisions.compared.yara_rule_id, $scope.selectedRevisions.compared.revision)
                                .then(function (response) {
                                    $scope.selectedRevisions.compared.yara_rule_string = response;
                                    $scope.calculateRevisionDiff();
                                }, function (error) {
                                    growl.error(error.data, {ttl: -1});
                                });
                        } else {
                            $scope.calculateRevisionDiff();
                        }
                    } else {
                        $scope.calculateRevisionDiff();
                    }
                }
            );
        }]);
