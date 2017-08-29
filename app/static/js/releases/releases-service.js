'use strict';

angular.module('InquestKB')
    .factory('Release', ['$resource', function ($resource) {
        return $resource('InquestKB/releases/:id', {}, {
            'query': {method: 'GET', isArray: true},
            'get': {method: 'GET'}
        });
    }]);
