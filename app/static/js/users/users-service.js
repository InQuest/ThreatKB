'use strict';

angular.module('InquestKB')
    .factory('Users', ['$resource', function ($resource) {
        return $resource('InquestKB/users/:id', {}, {
            'query': {method: 'GET', isArray: true},
            'get': {method: 'GET'}
        });
    }]);
