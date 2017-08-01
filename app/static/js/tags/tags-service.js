'use strict';

angular.module('InquestKB')
  .factory('Tags', ['$resource', function ($resource) {
    return $resource('InquestKB/tags/:id', {}, {
      'query': { method: 'GET', isArray: true},
      'get': { method: 'GET'},
      'update': { method: 'PUT'}
    });
  }]);
