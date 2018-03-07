'use strict';

angular.module('ThreatKB')
    .controller('Yara_ruleController', ['$scope', '$timeout', '$filter', '$http', '$uibModal', 'resolvedYara_rule', 'Yara_rule', 'Cfg_states', 'CfgCategoryRangeMapping', 'Users', 'growl', 'openModalForId', 'uiGridConstants', 'FileSaver', 'Blob',
        function ($scope, $timeout, $filter, $http, $uibModal, resolvedYara_rule, Yara_rule, Cfg_states, CfgCategoryRangeMapping, Users, growl, openModalForId, uiGridConstants, FileSaver, Blob) {

            $scope.yara_rules = resolvedYara_rule;

            $scope.cfg_states = Cfg_states.query();

            $scope.users = Users.query();

            $scope.clear_checked = function () {
                $scope.checked_indexes = [];
                $scope.checked_counter = 0;
                $scope.all_checked = false;
            };

            $scope.clear_checked();

            $scope.filterOptions = {
                filterText: ''
            };

            $scope.disable_multi_actions = function () {
                if ($scope.checked_counter < 1) {
                    return true;
                }
                return false;
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

            $scope.copy_rules = function () {
                var c = new Clipboard('.btn', {
                    text: function (trigger) {
                        var output = "";
                        for (var i = 0; i < $scope.checked_indexes.length; i++) {
                            if ($scope.checked_indexes[i]) {
                                output += $scope.yara_rules[i].yara_rule_string + "\n\n";
                            }
                        }
                        return output;
                    }
                })
                growl.info("Successfully copied " + $scope.checked_counter + " signatures to clipboard.", {ttl: 3})
            };

            $scope.download_rules = function () {
                var output = "";
                for (var i = 0; i < $scope.checked_indexes.length; i++) {
                    if ($scope.checked_indexes[i]) {
                        output += $scope.yara_rules[i].yara_rule_string + "\n\n";
                    }
                }
                try {
                    FileSaver.saveAs(new Blob([output], {type: "text/plain"}), "yara_rules.txt");
                }
                catch (error) {
                    growl.error("Error downloading signatures.", {ttl: -1});
                }
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

                        getPage();
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
                            field: 'checked',
                            displayName: "",
                            enableSorting: false,
                            width: "5%",
                            headerCellTemplate: '<BR><center><input style="vertical-align: middle;" type="checkbox" ng-model="grid.appScope.all_checked" ng-click="grid.appScope.toggle_checked()" /></center>',
                            cellTemplate: '<center><input type="checkbox" ng-model="grid.appScope.checked_indexes[grid.appScope.get_index_from_row(row)]" ng-change="grid.appScope.update_checked_counter(row)" /></center>'
                        },
                        {field: 'eventid', displayName: "Event ID", width: "10%", enableCellEditOnFocus: true},
                        {field: 'name', width: "30%", enableSorting: true},
                        {field: 'category', enableSorting: true},
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
                            + '<button confirmed-click="grid.appScope.delete(row.entity.id)"'
                            + ' ng-confirm-click="Are you sure you want to '
                            + 'inactivate this signature?" class="btn btn-sm btn-danger">'
                            + '<small>'
                            + '<span class="glyphicon glyphicon-remove-circle"></span>'
                            + '</small>'
                            + '</button>'
                            + '&nbsp;'
                            + '<button class="btn btn-sm">'
                            + '<small><span class="glyphicon glyphicon-link" style="font-size: 1.2em;"'
                            + 'title="Copy Yara Rule to clipboard" tooltip-placement="bottom"'
                            + 'uib-tooltip="Copied Yara Rule!"'
                            + 'tooltip-trigger="\'outsideClick\'"'
                            + 'ngclipboard data-clipboard-text="{{ row.entity.yara_rule_string }}"></span></small>'
                            + '</button>'
                            + '</div>'
                        }
                    ]
            };

            $scope.state = {};

            var getPage = function () {
                var url = '/ThreatKB/yara_rules?';
                url += 'page_number=' + (paginationOptions.pageNumber - 1);
                url += '&page_size=' + paginationOptions.pageSize;
                url += '&include_yara_string=1';
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
                        $scope.yara_rules = $scope.gridOptions.data;
                        $scope.clear_checked();
                        for (var i = 0; i < $scope.gridOptions.data.length; i++) {
                            $scope.checked_indexes.push(false);
                        }
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
                $scope.yara_rule = Yara_rule.resource.get({id: id, include_yara_string: 1});
                $scope.cfg_states = Cfg_states.query();
                $scope.users = Users.query();
                $scope.cfg_category_range_mapping = CfgCategoryRangeMapping.query();
                $scope.open(id);
            };

            $scope.delete = function (id) {
                Yara_rule.resource.delete({id: id}, function () {
                    //$scope.yara_rules = Yara_rule.resource.query();
                    getPage();
                });
            };

            $scope.save = function (id_or_rule) {
                var id = id_or_rule;
                if (typeof(id_or_rule) === "object") {
                    if (id_or_rule.merge) {
                        Yara_rule.merge_signature($scope.yara_rule.id, id_or_rule.id).then(function (data) {
                            growl.info("Successfully merged '" + $scope.yara_rule.name + "' into '" + id_or_rule.name + "'", {ttl: 3000});
                        }, function (error) {
                            growl.error(error, {ttl: -1})
                        })
                    } else {
                        id = id_or_rule.id;
                        $scope.yara_rule = id_or_rule;
                    }
                }

                if (typeof(id) === "number") {
                    Yara_rule.resource.update({id: id}, $scope.yara_rule, function () {
                        //$scope.yara_rules = Yara_rule.resource.query();
                        getPage();
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
                            if (typeof(entity.default) == "object") {
                                $scope.yara_rule.metadata_values[entity.key] = {value: entity.default.choice};
                            } else {
                                $scope.yara_rule.metadata_values[entity.key] = {value: entity.default};
                            }
                        }
                    }

                    Yara_rule.resource.save($scope.yara_rule, function () {
                        //$scope.yara_rules = Yara_rule.resource.query();
                        getPage();
                    });
                }
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
                    "addedTags": [],
                    "removedTags": [],
                    "comments": [],
                    "files": []
                };
            };

            $scope.open = function (id) {
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
                        }],
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

            getPage();
            if (openModalForId !== null) {
                $scope.update(openModalForId);
            }
        }])
    .controller('Yara_ruleSaveController', ['$scope', '$http', '$cookies', '$uibModalInstance', '$location', 'yara_rule', 'yara_rules', 'metadata', 'Cfg_states', 'Comments', 'Upload', 'Files', 'CfgCategoryRangeMapping', 'growl', 'Users', 'Tags', 'Yara_rule', 'Cfg_settings', 'Bookmarks', 'hotkeys',
        function ($scope, $http, $cookies, $uibModalInstance, $location, yara_rule, yara_rules, metadata, Cfg_states, Comments, Upload, Files, CfgCategoryRangeMapping, growl, Users, Tags, Yara_rule, Cfg_settings, Bookmarks, hotkeys) {

            $scope.yara_rule = yara_rule;
            $scope.yara_rules = yara_rules;
            $scope.metadata = metadata;
            $scope.yara_rule.new_comment = "";
            $scope.Comments = Comments;
            $scope.Files = Files;
            $scope.selected_signature = null;

            $scope.wrap_editor = ($cookies.get("wrap_editor") == "true");

            if ($scope.wrap_editor == null) {
                $scope.wrap_editor = false;
                var expireDate = new Date();
                expireDate.setDate(expireDate.getDate() + 365);
                $cookies.put("wrap_editor", $scope.wrap_editor, {expires: expireDate});
            }

            $scope.change_wrap_editor = function () {
                $scope.editor_options.lineWrapping = $scope.wrap_editor;
                var expireDate = new Date();
                expireDate.setDate(expireDate.getDate() + 365);
                $cookies.put("wrap_editor", $scope.wrap_editor, {expires: expireDate});
            };

            $scope.save_artifact = function () {
                Yara_rule.resource.update({id: $scope.yara_rule.id}, $scope.yara_rule,
                    function (data) {
                        if (!data) {
                            growl.error(error, {ttl: -1});
                        } else {
                            growl.info("Successfully saved signature '" + $scope.yara_rule.name + "'.", {ttl: 2000});
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
                combo: 'ctrl+x',
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
                    $scope.wrap_editor = !$scope.wrap_editor;
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
                return $location.absUrl() + "/" + id;
            };

            $scope.cfg_states = Cfg_states.query();
            $scope.cfg_category_range_mapping = CfgCategoryRangeMapping.query();
            $scope.do_not_bump_revision = false;

            $scope.just_opened = true;
            $scope.negTestDir = Cfg_settings.get({key: "NEGATIVE_TESTING_FILE_DIRECTORY"});
            $scope.testingPos = false;
            $scope.testingNeg = false;

            $scope.print_comment = function (comment) {
                return comment.comment.replace(/(?:\r\n|\r|\n)/g, "<BR>");
            };

            $scope.editor_options = {
                lineNumbers: true,
                lineWrapping: $scope.wrap_editor,
                mode: 'yara'
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
                    })
                });
            };

            $scope.$watch('files', function () {
                $scope.upload($scope.files);
            });

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
                                growl.info('Success ' + JSON.stringify(resp.data, null, 2), {ttl: 3000});
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
                $uibModalInstance.close($scope.yara_rule);
            };

            $scope.cancel = function () {
                $uibModalInstance.dismiss('cancel');
            };

            $scope.addedTag = function ($tag) {
                $scope.yara_rule.addedTags.push($tag)
            };

            $scope.removedTag = function ($tag) {
                $scope.yara_rule.removedTags.push($tag)
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
                    return $http.get('/ThreatKB/test_yara_rule/' + id, {cache: false}).then(function (response) {
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
                    return $http.get('/ThreatKB/test_yara_rule/' + id + '?negative=1', {cache: false})
                        .then(function (response) {
                            var testResponse = response.data;
                            var growlMsg = "Clean Test Summary<br />"
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
                            $scope.testingNeg = false;
                            return true;
                        }, function (error) {
                            growl.error(error.data, {ttl: 3000});
                            $scope.testingNeg = false;
                        });
                }
            };

            $scope.merge_signature = function () {
                if (!$scope.selected_signature) {
                    return;
                }

                $scope.selected_signature.merge = true;
                $uibModalInstance.close($scope.selected_signature);
            };

        }]);
