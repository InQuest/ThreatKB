'use strict';

angular.module('ThreatKB')
  .factory('Tags', ['$resource', function ($resource) {
      return $resource('ThreatKB/tags/:id', {}, {
      'query': { method: 'GET', isArray: true},
      'get': { method: 'GET'},
      'update': { method: 'PUT'}
    });
  }]);
