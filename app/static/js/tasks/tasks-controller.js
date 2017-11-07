'use strict';

angular.module('ThreatKB')
    .controller('TasksController', ['$scope', '$uibModal', 'resolvedTask', 'Task', 'Cfg_states', 'growl', 'Users', 'openModalForId',
        function ($scope, $uibModal, resolvedTask, Task, Cfg_states, growl, Users, openModalForId) {

            $scope.tasks = resolvedTask;

            $scope.users = Users.query();

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
                    $scope.tasks = Task.query();
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
                        $scope.tasks = Task.query();
                        //$scope.clear();
                    });
                } else {
                    Task.save($scope.task, function () {
                        $scope.tasks = Task.query();
                        //$scope.clear();
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

            if (openModalForId !== null) {
                $scope.update(openModalForId);
            }
        }])
    .controller('TaskSaveController', ['$scope', '$http', '$uibModalInstance', 'task', 'Comments', 'Cfg_states', 'Import', 'growl', 'blockUI', 'AuthService',
        function ($scope, $http, $uibModalInstance, task, Comments, Cfg_states, Import, growl, blockUI, AuthService) {
            $scope.task = task;
            $scope.task.new_comment = "";
            $scope.Comments = Comments;
            $scope.current_user = AuthService.getUser();

            if ($scope.task.$promise !== undefined) {
                $scope.task.$promise.then(function (result) {
                }, function (errorMsg) {
                    growl.error("Task Not Found", {ttl: -1});
                    $uibModalInstance.dismiss('cancel');
                });
            }

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
