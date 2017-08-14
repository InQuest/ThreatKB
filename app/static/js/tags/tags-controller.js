'use strict';

angular.module('InquestKB')
  .controller('TagsController', ['$scope', '$uibModal', 'resolvedTags', 'Tags',
    function ($scope, $uibModal, resolvedTags, Tags) {

      $scope.tags = resolvedTags;

      $scope.create = function () {
        $scope.clear();
        $scope.open();
      };

      $scope.update = function (id) {
        $scope.tags = Tags.get({id: id});
        $scope.open(id);
      };

      $scope.delete = function (id) {
        Tags.delete({id: id},
          function () {
            $scope.tags = Tags.query();
          });
      };

      $scope.save = function (id) {
        if (id) {
          Tags.update({id: id}, $scope.tags,
            function () {
              $scope.tags = Tags.query();
//              $scope.clear();
            });
        } else {
          Tags.save($scope.tags,
            function () {
              $scope.tags = Tags.query();
//              $scope.clear();
            });
        }
      };

      $scope.clear = function () {
        $scope.tags = {
          
          "text": "",
          
          "id": ""
        };
      };

      $scope.open = function (id) {
        var tagsSave = $uibModal.open({
          templateUrl: 'tags-save.html',
          controller: 'TagsSaveController',
          resolve: {
            tags: function () {
              return $scope.tags;
            }
          }
        });

        tagsSave.result.then(function (entity) {
          $scope.tags = entity;
          $scope.save(id);
        });
      };
    }])
  .controller('TagsSaveController', ['$scope', '$uibModalInstance', 'tags',
    function ($scope, $uibModalInstance, tags) {
      $scope.tags = tags;

      

      $scope.ok = function () {
        $uibModalInstance.close($scope.tags);
      };

      $scope.cancel = function () {
        $uibModalInstance.dismiss('cancel');
      };
    }]);
