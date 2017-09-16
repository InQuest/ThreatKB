'use strict';

angular.module('ThreatKB')
    .controller('Yara_ruleController', ['$scope', '$filter', '$http', '$uibModal', 'resolvedYara_rule', 'Yara_rule', 'Cfg_states', 'CfgCategoryRangeMapping', 'Users', 'uiGridConstants',
        function ($scope, $filter, $http, $uibModal, resolvedYara_rule, Yara_rule, Cfg_states, CfgCategoryRangeMapping, Users, uiGridConstants) {

            $scope.yara_rules = resolvedYara_rule;

            $scope.users = Users.query();

            $scope.cfg_states = Cfg_states.query();

            $scope.filterOptions = {
                filterText: ''
            };

            $scope.gridOptions = {
                enableFiltering: true,
                onRegisterApi: function (gridApi) {
                    $scope.gridApi = gridApi;
                },
                columnDefs:
                    [
                        {field: 'signature_id'},
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
                            enableCellEdit: false,
                            enableFiltering: false,
                            cellTemplate: '<div style="text-align: center;">'
                            + '<button type="button" ng-click="grid.appScope.update(row.entity.id)"'
                            + ' class="btn btn-sm">'
                            + '<small><span class="glyphicon glyphicon-pencil"></span>'
                            + '</small>'
                            + '</button>'
                            + '<button ng-click="grid.appScope.delete(row.entity.id)"'
                            + ' ng-confirm-click="Are you sure you want to '
                            + 'inactivate this signature?" class="btn btn-sm btn-danger">'
                            + '<small>'
                            + '<span class="glyphicon glyphicon-remove-circle"></span>'
                            + '</small>'
                            + '</button></div>'
                        }
                    ]
            };

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
                $scope.yara_rule = Yara_rule.get({id: id});
                $scope.cfg_states = Cfg_states.query();
                $scope.users = Users.query();
                $scope.cfg_category_range_mapping = CfgCategoryRangeMapping.query();
                $scope.open(id);
            };

            $scope.delete = function (id) {
                Yara_rule.delete({id: id}, function () {
                    $scope.yara_rules = Yara_rule.query();
                    $scope.gridOptions.data = $scope.yara_rules
                });
            };

            $scope.save = function (id_or_rule) {
                var id = id_or_rule;
                if (typeof(id_or_rule) === "object") {
                    id = id_or_rule.id;
                    $scope.yara_rule = id_or_rule;
                }

                if (id) {
                    Yara_rule.update({id: id}, $scope.yara_rule, function () {
                        $scope.yara_rules = Yara_rule.query();
                        $scope.gridOptions.data = $scope.yara_rules
                    });
                } else {
                    Yara_rule.save($scope.yara_rule, function () {
                        $scope.yara_rules = Yara_rule.query();
                        $scope.gridOptions.data = $scope.yara_rules
                    });
                }
            };

            $scope.clear = function () {
                $scope.yara_rule = {
                    "date_created": "",
                    "date_modified": "",
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
                    "reference_text": "",
                    "condition": "",
                    "strings": "",
                    "signature_id": "",
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
                        }
                    }
                });

                yara_ruleSave.result.then(function (entity) {
                    $scope.yara_rule = entity;
                    $scope.save(id);
                });
            };
        }])
    .controller('Yara_ruleSaveController', ['$scope', '$http', '$uibModalInstance', 'yara_rule', 'Cfg_states', 'Comments', 'Upload', 'Files', 'CfgCategoryRangeMapping', 'growl', 'Users',
        function ($scope, $http, $uibModalInstance, yara_rule, Cfg_states, Comments, Upload, Files, CfgCategoryRangeMapping, growl, Users) {
            $scope.yara_rule = yara_rule;
            $scope.yara_rule.new_comment = "";
            $scope.Comments = Comments;
            $scope.Files = Files;

            $scope.cfg_states = Cfg_states.query();
            $scope.cfg_category_range_mapping = CfgCategoryRangeMapping.query();
            $scope.do_not_bump_revision = false;

            $scope.just_opened = true;
            $scope.testing = false;

            $scope.print_comment = function (comment) {
                return comment.comment.replace(/(?:\r\n|\r|\n)/g, "<BR>");
            };

            $scope.editor_options = {
                lineWrapping: false,
                lineNumbers: true,
                mode: 'yara'
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
                return $http.get('/ThreatKB/tags', {cache: false}).then(function (response) {
                    var tags = response.data;
                    return tags.filter(function (tag) {
                        return tag.text.toLowerCase().indexOf(query.toLowerCase()) !== -1;
                    }, function (error) {
                        growl.error(error.data, {ttl: -1});
                    });
                });
            };

            $scope.$watch('testing', function () {
                $scope.testButtonText = $scope.testing ? 'Testing...' : 'Test Signature Now';
            });

            $scope.testSignature = function (id) {
                if (!$scope.testing) {
                    $scope.testing = true;
                    return $http.get('/ThreatKB/test_yara_rule/' + id, {cache: false}).then(function (response) {
                        var testResponse = response.data;
                        growl.info("Success!<br />"
                            + "---------------------<br/>"
                            + "Total Files: " + testResponse['files_tested'] + "<br/>"
                            + "Matches Found: " + testResponse['files_matched'] + "<br/>"
                            + "Tests Killed: " + testResponse['tests_terminated'],
                            {ttl: 3000});
                        $scope.testing = false;
                        return true;
                    }, function (error) {
                        growl.error(error.data, {ttl: -1});
                    });
                }
            }
        }]);
