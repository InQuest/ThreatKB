'use strict';

angular.module('InquestKB').controller('ImportController',
    ['$scope', '$location', 'Import', 'growl',
        function ($scope, $location, Import, growl) {

            $scope.commit_artifacts = function () {
                Import.commit_artifacts($scope.artifacts).then(function (data) {
                    growl.info("Successfully committed " + data.length + " artifacts.", {ttl: 3000});
                    $scope.clear();
                });
            }
            $scope.import_artifacts = function () {

                Import.import_artifacts($scope.import_text, $scope.autocommit).then(function (data) {
                        if ($scope.autocommit) {
                            growl.info("Successfully committed " + data.length + " artifacts.", {ttl: 3000});
                            $scope.clear();
                        } else {
                            $scope.artifacts = data;
                        }


                    }
                );
            };

            $scope.clear = function () {
                $scope.import_text = "";
                $scope.autocommit = false;
                $scope.artifacts = null;
            };

        }]);

