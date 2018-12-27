'use strict';

angular.module('ThreatKB')
    .factory('Users', ['$resource', function ($resource) {
        return $resource('/ThreatKB/users/:id', {}, {
            'query': {method: 'GET', isArray: true},
            'get': {method: 'GET'},
            'delete': {method: 'DELETE'}
        });
    }]);
