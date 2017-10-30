'use strict';

angular.module('ThreatKB')
    .controller('Yara_ruleController', ['$scope', '$filter', '$http', '$uibModal', 'resolvedYara_rule', 'Yara_rule', 'Cfg_states', 'CfgCategoryRangeMapping', 'Users', 'growl',
        function ($scope, $filter, $http, $uibModal, resolvedYara_rule, Yara_rule, Cfg_states, CfgCategoryRangeMapping, Users, growl) {

            $scope.yara_rules = resolvedYara_rule;

            $scope.users = Users.query();

            $scope.filterOptions = {
                filterText: ''
            };

            $scope.gridOptions = {
                enableFiltering: true,
                onRegisterApi: function (gridApi) {
                    $scope.gridApi = gridApi;
                },
                rowHeight: 35,
                columnDefs:
                    [
                        {field: 'eventid', displayName: "Event ID"},
                        {field: 'name'},
                        {field: 'category'},
                        {field: 'state'},
                        {
                            field: 'owner_user.email',
                            displayName: 'Owner',
                            width: '20%',
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
                            + 'inactivate this signature ({{ row.entity.name }})?" class="btn btn-sm btn-danger">'
                            + '<small>'
                            + '<span class="glyphicon glyphicon-remove-circle"></span>'
                            + '</small>'
                            + '</button></div>'
                        }
                    ]
            };

            $scope.state = {};

            $scope.refreshData = function () {
                $scope.gridOptions.data = $filter('filter')($scope.yara_rules, $scope.searchText, undefined);
            };

            $http.get('/ThreatKB/yara_rules')
                .then(function (response) {
                    $scope.gridOptions.data = response.data;
                }, function (error) {
                });

            $scope.create = function () {
                $scope.clear();
                $scope.open();
            };

            $scope.update = function (id) {
                $scope.yara_rule = Yara_rule.resource.get({id: id});
                $scope.cfg_states = Cfg_states.query();
                $scope.users = Users.query();
                $scope.cfg_category_range_mapping = CfgCategoryRangeMapping.query();
                $scope.open(id);
            };

            $scope.delete = function (id) {
                Yara_rule.resource.delete({id: id}, function () {
                    $scope.yara_rules = Yara_rule.resource.query();
                    $scope.gridOptions.data = $scope.yara_rules;
                    $scope.refreshData();
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
                        $scope.yara_rules = Yara_rule.resource.query();
                        $scope.gridOptions.data = $scope.yara_rules;
                        $scope.refreshData();
                    });
                } else {
                    Yara_rule.resource.save($scope.yara_rule, function () {
                        $scope.yara_rules = Yara_rule.resource.query();
                        $scope.gridOptions.data = $scope.yara_rules;
                        $scope.refreshData();
                    });
                }
            };

            $scope.clear = function () {
                $scope.yara_rule = {
                    "creation_date": "",
                    "last_revision_date": "",
                    "state": "",
                    "name": "",
                    "test_status": "",
                    "confidence": "",
                    "severity": "",
                    "description": "",
                    "category": "",
                    "file_type": "",
                    "subcategory1": "",
                    "subcategory2": "",
                    "subcategory3": "",
                    "reference_link": "",
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
                    resolve: {
                        yara_rule: function () {
                            return $scope.yara_rule;
                        },
                        yara_rules: function () {
                            return $scope.yara_rules;
                        }
                    },
                    size: 'lg'
                });

                yara_ruleSave.result.then(function (entity) {
                    if (entity.merge) {
                        $scope.save(entity);
                    } else {
                        $scope.yara_rule = entity;
                        $scope.save(id);
                    }
                });
            };
        }])
    .controller('Yara_ruleSaveController', ['$scope', '$http', '$uibModalInstance', 'yara_rule', 'yara_rules', 'Cfg_states', 'Comments', 'Upload', 'Files', 'CfgCategoryRangeMapping', 'growl', 'Users', 'Tags', 'Yara_rule', 'Cfg_settings',
        function ($scope, $http, $uibModalInstance, yara_rule, yara_rules, Cfg_states, Comments, Upload, Files, CfgCategoryRangeMapping, growl, Users, Tags, Yara_rule, Cfg_settings) {

            $scope.yara_rule = yara_rule;
            $scope.yara_rules = yara_rules;
            $scope.yara_rule.new_comment = "";
            $scope.Comments = Comments;
            $scope.Files = Files;
            $scope.selected_signature = null;

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
                lineWrapping: false,
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
                                })
                            }, function (resp) {
                                console.log('Error status: ' + resp.status);
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
