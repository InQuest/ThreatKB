// 'use strict';
//
// angular.module('ThreatKB')
//   .controller('Tags_mappingController', ['$scope', 'resolvedTags_mapping', 'Tags_mapping',
//     function ($scope, resolvedTags_mapping, Tags_mapping) {
//
//       $scope.tags_mapping = resolvedTags_mapping;
//
//       $scope.update = function (source, id, tags) {
//         console.log("update tags: " + tags);
//         // $scope.tags_mapping = Tags_mapping.get({id: id});
//       };
//
//       $scope.delete = function (id) {
//         Tags_mapping.delete({id: id},
//           function () {
//             $scope.tags_mapping = Tags_mapping.query();
//           });
//       };
//
//       $scope.save = function (id) {
//         if (id) {
//           Tags_mapping.update({id: id}, $scope.tags_mapping,
//             function () {
//               $scope.tags_mapping = Tags_mapping.query();
// //              $scope.clear();
//             });
//         } else {
//           Tags_mapping.save($scope.tags_mapping,
//             function () {
//               $scope.tags_mapping = Tags_mapping.query();
// //              $scope.clear();
//             });
//         }
//       };
//     }]);
