'use strict';

angular.module('InquestKB')
  .controller('Tags_mappingController', ['$scope', '$modal', 'resolvedTags_mapping', 'Tags_mapping',
    function ($scope, $modal, resolvedTags_mapping, Tags_mapping) {

      $scope.tags_mapping = resolvedTags_mapping;

      $scope.create = function () {
        $scope.clear();
        $scope.open();
      };

      $scope.update = function (id) {
        $scope.tags_mapping = Tags_mapping.get({id: id});
        $scope.open(id);
      };

      $scope.delete = function (id) {
        Tags_mapping.delete({id: id},
          function () {
            $scope.tags_mapping = Tags_mapping.query();
          });
      };

      $scope.save = function (id) {
        if (id) {
          Tags_mapping.update({id: id}, $scope.tags_mapping,
            function () {
              $scope.tags_mapping = Tags_mapping.query();
//              $scope.clear();
            });
        } else {
          Tags_mapping.save($scope.tags_mapping,
            function () {
              $scope.tags_mapping = Tags_mapping.query();
//              $scope.clear();
            });
        }
      };

      $scope.clear = function () {
        $scope.tags_mapping = {
          
          "source_table": "",

          "source_id": "",

          "tag_id": "",

          "id": ""
        };
      };

      $scope.open = function (id) {
        var tags_mappingSave = $modal.open({
          templateUrl: 'tags_mapping-save.html',
          controller: 'Tags_mappingSaveController',
          resolve: {
            tags_mapping: function () {
              return $scope.tags_mapping;
            }
          }
        });

        tags_mappingSave.result.then(function (entity) {
          $scope.tags_mapping = entity;
          $scope.save(id);
        });
      };
    }])
  .controller('Tags_mappingSaveController', ['$scope', '$modalInstance', 'tags_mapping',
    function ($scope, $modalInstance, tags_mapping) {
      $scope.tags_mapping = tags_mapping;

      

      $scope.ok = function () {
        $modalInstance.close($scope.tags_mapping);
      };

      $scope.cancel = function () {
        $modalInstance.dismiss('cancel');
      };
    }]);
