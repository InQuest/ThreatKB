'use strict';

angular.module('InquestKB')
    .controller('Yara_ruleController', ['$scope', '$modal', 'resolvedYara_rule', 'Yara_rule', 'Cfg_states', 'Comments',
        function ($scope, $modal, resolvedYara_rule, Yara_rule, Cfg_states, Comments) {

            $scope.yara_rules = resolvedYara_rule;
            $scope.create = function () {
                $scope.clear();
                $scope.open();
            };

            $scope.update = function (id) {
                $scope.yara_rule = Yara_rule.get({id: id});
                $scope.cfg_states = Cfg_states.query();
                $scope.yara_rule.comments = Comments.resource.query( {entity_type: Comments.entity_mapping.SIGNATURE, entity_id: id});
                $scope.open(id);
            };

            $scope.delete = function (id) {
                Yara_rule.delete({id: id},
                    function () {
                        $scope.yara_rules = Yara_rule.query();
                    });
            };

            $scope.save = function (id) {
                if (id) {
                    Yara_rule.update({id: id}, $scope.yara_rule,
                        function () {
                            $scope.yara_rules = Yara_rule.query();
                            //$scope.clear();
                        });
                } else {
                    Yara_rule.save($scope.yara_rule,
                        function () {
                            $scope.yara_rules = Yara_rule.query();
                            //$scope.clear();
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

                    "id": "",

                    "comments": []
                };
            };

            $scope.open = function (id) {
                var yara_ruleSave = $modal.open({
                    templateUrl: 'yara_rule-save.html',
                    controller: 'Yara_ruleSaveController',
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
    .controller('Yara_ruleSaveController', ['$scope', '$modalInstance', 'yara_rule', 'Cfg_states', 'Comments',
        function ($scope, $modalInstance, yara_rule, Cfg_states, Comments) {
            $scope.yara_rule = yara_rule;

            $scope.ok = function () {
                $modalInstance.close($scope.yara_rule);
            };

            $scope.cancel = function () {
                $modalInstance.dismiss('cancel');
            };

            $scope.add_comment = function(){
                Comments.save($scope.new_comment, )
            }
        }]);
