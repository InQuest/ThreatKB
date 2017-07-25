'use strict';

angular.module('InquestKB')
    .factory('C2dns', ['$resource', function ($resource) {
        return $resource('InquestKB/c2dns/:id', {}, {
            'query': {method: 'GET', isArray: true},
            'get': {method: 'GET'},
            'update': {method: 'PUT'}
        });
    }]);
