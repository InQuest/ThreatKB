
angular.module('InquestKB')
  .factory('Comments', ['$resource', function ($resource) {
    return {resource: $resource('InquestKB/comments/:id', {}, {
      'query': { method: 'GET', isArray: true},
      'get': { method: 'GET'},
      'update': { method: 'PUT'}
    }),
        entity_mapping: {IP: 3, DNS: 2, SIGNATURE: 1}}
        ;
  }]);
