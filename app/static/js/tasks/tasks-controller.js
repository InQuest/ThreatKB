'use strict';

angular.module('ThreatKB')
    .controller('TasksController', ['$scope', '$timeout', '$filter', '$http', '$uibModal', 'resolvedTask', 'Task', 'Cfg_states', 'growl', 'Users', 'openModalForId', 'uiGridConstants',
        function ($scope, $timeout, $filter, $http, $uibModal, resolvedTask, Task, Cfg_states, growl, Users, openModalForId, uiGridConstants) {

            $scope.tasks = resolvedTask;

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
                            if (column.filters[0].term !== undefined && column.filters[0].term !== null && column.filters[0].term.length >= 3) {
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
                        {
                            field: 'title',
                            displayName: 'Title',
                            enableSorting: true
                        },
                        {
                            field: 'state',
                            displayName: 'State',
                            width: '180',
                            enableSorting: true,
                            cellTemplate: '<ui-select append-to-body="true" ng-model="row.entity.state"'
                            + ' on-select="grid.appScope.save(row.entity)">'
                            + '<ui-select-match placeholder="Select a state ...">'
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
                            width: '180',
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
                            + 'delete this task?" class="btn btn-sm btn-danger">'
                            + '<small>'
                            + '<span class="glyphicon glyphicon-remove-circle"></span>'
                            + '</small>'
                            + '</button></div>'
                        }
                    ]
            };

            var getPage = function () {
                var url = '/ThreatKB/tasks?';
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
                $scope.task = Task.get({id: id});
                $scope.cfg_states = Cfg_states.query();
                $scope.users = Users.query();
                $scope.open(id);
            };

            $scope.delete = function (id) {
                Task.delete({id: id}, function () {
                    getPage();
                });
            };

            $scope.save = function (id_or_ip) {
                var id = id_or_ip;
                if (typeof(id_or_ip) === "object") {
                    id = id_or_ip.id;
                    $scope.task = id_or_ip;
                }

                if (id) {
                    Task.update({id: id}, $scope.task, function () {
                        getPage();
                    }, function (error) {
                        growl.error(error.data, {ttl: -1});
                    });
                } else {
                    Task.save($scope.task, function () {
                        getPage();
                    }, function (error) {
                        growl.error(error.data, {ttl: -1});
                    });
                }
            };

            $scope.clear = function () {
                $scope.task = {
                    title: "",
                    description: "",
                    final_artifact: "",
                    date_created: "",
                    date_modified: "",
                    state: "",
                    id: ""
                };
            };

            $scope.open = function (id) {
                var taskSave = $uibModal.open({
                    templateUrl: 'task-save.html',
                    controller: 'TaskSaveController',
                    size: 'lg',
                    backdrop: 'static',
                    resolve: {
                        task: function () {
                            return $scope.task;
                        }
                    }
                });

                taskSave.result.then(function (entity) {
                    $scope.task = entity;
                    $scope.save(id);
                });
            };

            getPage();

            if (openModalForId !== null) {
                $scope.update(openModalForId);
            }
        }])
    .controller('TaskSaveController', ['$scope', '$http', '$uibModalInstance', '$location', 'task', 'Comments', 'Cfg_states', 'Import', 'growl', 'blockUI', 'AuthService', 'Bookmarks', 'hotkeys', 'Users',
        function ($scope, $http, $uibModalInstance, $location, task, Comments, Cfg_states, Import, growl, blockUI, AuthService, Bookmarks, hotkeys, Users) {
            $scope.task = task;
            $scope.task.new_comment = "";
            $scope.Comments = Comments;
            $scope.current_user = AuthService.getUser();

            $scope.users = Users.query();

            hotkeys.bindTo($scope)
                .add({
                    combo: 'ctrl+s',
                    description: 'Save',
                    allowIn: ['INPUT', 'SELECT', 'TEXTAREA'],
                    callback: function () {
                        $scope.ok();
                    }
                }).add({
                    combo: 'ctrl+x',
                    description: 'Escape',
                    allowIn: ['INPUT', 'SELECT', 'TEXTAREA'],
                    callback: function () {
                        $scope.cancel();
                    }
                });

            if ($scope.task.$promise !== undefined) {
                $scope.task.$promise.then(function (result) {
                }, function (errorMsg) {
                    growl.error("Task Not Found", {ttl: -1});
                    $uibModalInstance.dismiss('cancel');
                });
            }

            $scope.bookmark = function (id) {
                Bookmarks.createBookmark(Bookmarks.ENTITY_MAPPING.TASK, id).then(function (data) {
                    $scope.task.bookmarked = true;
                });
            };

            $scope.unbookmark = function (id) {
                Bookmarks.deleteBookmark(Bookmarks.ENTITY_MAPPING.TASK, id).then(function (data) {
                    $scope.task.bookmarked = false;
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

            $scope.extract_artifact = function () {
                blockUI.start("Extracting artifact...");
                Import.import_artifacts($scope.task.final_artifact, true, null, null, $scope.current_user.id).then(function (data) {
                        blockUI.stop();
                        var message = "";
                        if (data.committed) {
                            message = "Successfully committed " + data.committed.length + " artifacts.<BR><BR>";
                        }

                        growl.info(message, {
                            ttl: 3000,
                            disableCountDown: true
                        });
                    }, function (error) {
                    blockUI.stop();
                        growl.error(error.data, {ttl: -1});
                    }
                );

            };

            $scope.print_comment = function (comment) {
                return comment.comment.replace(/(?:\r\n|\r|\n)/g, "<BR>");
            };

            $scope.add_comment = function (id) {
                if (!$scope.task.new_comment) {
                    return;
                }

                $scope.Comments.resource.save({
                    comment: $scope.task.new_comment,
                    entity_type: Comments.ENTITY_MAPPING.TASK,
                    entity_id: id
                }, function () {
                    $scope.task.new_comment = "";
                    $scope.task.comments = $scope.Comments.resource.query({
                        entity_type: Comments.ENTITY_MAPPING.TASK,
                        entity_id: id
                    })
                });
            };

            $scope.ok = function () {
                $uibModalInstance.close($scope.task);
            };

            $scope.cancel = function () {
                $uibModalInstance.dismiss('cancel');
            };
        }]);
