'use strict';

angular.module('InquestKB').controller('ImportController',
    ['$scope', '$location', 'Import', 'growl', 'Cfg_states',
        function ($scope, $location, Import, growl, Cfg_states) {

            $scope.cfg_states = Cfg_states.query();
            $scope.shared_state = {};

            $scope.update_commit_counter = function (index) {
                if ($scope.checked_indexes[index]) {
                    $scope.commit_counter += 1;
                } else {
                    $scope.commit_counter -= 1;
                }
            };

            $scope.uncheck_all = function () {
                for (var i = 0; i < $scope.checked_indexes.length; i++) {
                    $scope.checked_indexes[i] = false;
                }
                $scope.commit_counter = 0;
            };

            $scope.check_all = function () {
                for (var i = 0; i < $scope.checked_indexes.length; i++) {
                    $scope.checked_indexes[i] = true;
                }
                $scope.commit_counter = $scope.checked_indexes.length;
            };

            $scope.commit_artifacts = function () {
                var artifacts_to_commit = [];
                for (var i = 0; i < $scope.artifacts.length; i++) {
                    if ($scope.checked_indexes[i]) {
                        artifacts_to_commit.push($scope.artifacts[i]);
                    }
                }

                Import.commit_artifacts(artifacts_to_commit, $scope.shared_reference, $scope.shared_state.state.state).then(function (data) {
                    var message = "";
                    if (data.committed) {
                        message = "Successfully committed " + data.committed.length + " artifacts.<BR><BR>";
                    }
                    if (data.duplicates) {
                        message += "There were " + data.duplicates.length + " duplicates that were not committed.<BR><BR>";
                        for (var duplicate in data.duplicates) {
                            message += data.duplicates[key].artifact + "<BR>";
                        }
                    }

                    growl.info(message, {
                        ttl: 3000,
                        disableCountDown: true
                    });
                    $scope.clear();
                });
            }

            $scope.import_artifacts = function () {
                if ($scope.shared_state.state === undefined) {
                    $scope.shared_state.state = {};
                }

                Import.import_artifacts($scope.import_text, $scope.autocommit, $scope.shared_reference, $scope.shared_state.state.state).then(function (data) {
                        if ($scope.autocommit) {
                            var message = "";
                            if (data.committed) {
                                message = "Successfully committed " + data.committed.length + " artifacts.<BR><BR>";
                            }
                            if (data.duplicates) {
                                message += "There were " + data.duplicates.length + " duplicates that were not committed.<BR><BR>";
                                for (var key in data.duplicates) {
                                    message += data.duplicates[key].artifact + "<BR>";
                                }
                            }

                            growl.info(message, {
                                ttl: 3000,
                                disableCountDown: true
                            });
                            $scope.clear();
                        } else {
                            if (data.length > 0) {
                                $scope.artifacts = data;
                                $scope.checked_indexes = [];
                                for (var i = 0; i < $scope.artifacts.length; i++) {
                                    $scope.checked_indexes.push(true);
                                }
                                $scope.commit_counter = $scope.artifacts.length;
                            } else {
                                growl.info("No artifacts extracted from text.", {ttl: 3000, disableCountDown: true})
                                $scope.clear();
                            }
                        }
                    }, function (error) {
                    growl.error(error.data, {ttl: -1});
                    }
                );
            };

            $scope.clear = function () {
                $scope.import_text = "";
                $scope.autocommit = false;
                $scope.artifacts = null;
                $scope.checked_indexes = [];
                $scope.shared_reference = "";
                $scope.cfg_states = Cfg_states.query();
                $scope.shared_state = {};
            };

        }]);

