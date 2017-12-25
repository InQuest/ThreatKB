'use strict';

angular.module('ThreatKB')
    .controller('MetadataController', ['$scope', '$rootScope', '$uibModal', 'resolvedMetadatas', 'Metadata', 'Comments',
        function ($scope, $rootScope, $uibModal, resolvedMetadatas, Metadata, Comments) {

            $scope.metadatas = resolvedMetadatas;
            $scope.types = [{value: "string"},
                {value: "integer"}, {value: "date"}, {value: "multiline_comment"}];
            $scope.show_in_table_options = [{key: "Yes", value: 1}, {key: "No", value: 0}];
            $scope.artifact_type_options = $rootScope.ENTITY_MAPPING_REVERSE;

            $scope.artifact_type_to_string = function (type_) {
                return $rootScope.ENTITY_MAPPING_REVERSE[type_].value;
            };

            $scope.show_in_table_to_string = function (show_in_table) {
                for (var i = 0; i < $scope.show_in_table_options.length; i++) {
                    var obj = $scope.show_in_table_options[i];
                    if (obj.value == show_in_table) {
                        return obj.key;
                    }
                }
            };

            $scope.change_show_in_table_option = function (selected) {
                $scope.show_in_table = $scope.show_in_table_options[selected];
            }

            $scope.create = function () {
                $scope.clear();
                $scope.open();
            };

            $scope.delete = function (id) {
                Metadata.delete({id: id},
                    function () {
                        $scope.metadatas = Metadata.query();
                    });
            };

            $scope.save = function (id) {
                if (id) {
                    Metadata.update({id: id}, $scope.metadata,
                        function () {
                            $scope.metadatas = Metadata.query();
                            //$scope.clear();
                        });
                } else {
                    Metadata.save($scope.metadata,
                        function () {
                            $scope.metadatas = Metadata.query();
                            //$scope.clear();
                        });
                }
            };

            $scope.clear = function () {
                $scope.metadata = {
                    "key": "",
                    "id": "",
                    "type": "",
                    "artifact_type": "",
                    "default": "",
                    "show_in_table": "",
                };
            };

            $scope.open = function (id) {
                var metadataSave = $uibModal.open({
                    templateUrl: 'metadata-save.html',
                    controller: 'MetadataSaveController',
                    resolve: {
                        metadata: function () {
                            return $scope.metadata;
                        },
                        types: function () {
                            return $scope.types;
                        },
                        show_in_table_options: function () {
                            return $scope.show_in_table_options;
                        },
                        artifact_type_options: function () {
                            return $scope.artifact_type_options;
                        }
                    }
                });

                metadataSave.result.then(function (entity) {
                    $scope.metadata = entity;
                    $scope.save(id);
                });
            };
        }])
    .controller('MetadataSaveController', ['$scope', '$rootScope', '$uibModalInstance', 'metadata', 'types', 'show_in_table_options', 'artifact_type_options', 'Metadata', 'Comments',
        function ($scope, $rootScope, $uibModalInstance, metadata, types, show_in_table_options, artifact_type_options, Metadata, Comments) {
            $scope.metadata = metadata;
            $scope.types = types;
            $scope.show_in_table_options = show_in_table_options;
            $scope.artifact_type_options = artifact_type_options;

            $scope.change_show_in_table_option = function (selected) {
                $scope.metadata.show_in_table = selected.value;
            }

            $scope.change_type_option = function (selected) {
                $scope.metadata.type = selected.value;
            }

            $scope.change_artifact_type_option = function (selected) {
                $scope.metadata.artifact_type = selected.key;
                $scope.artifact_type = selected.value;
            }

            $scope.artifact_type_to_string = function (type_) {
                return $rootScope.ENTITY_MAPPING_REVERSE[type_];
            };

            $scope.ok = function () {
                $uibModalInstance.close($scope.metadata);
            };

            $scope.cancel = function () {
                $uibModalInstance.dismiss('cancel');
            };
        }]);
