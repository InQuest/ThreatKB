'use strict';

angular.module('ThreatKB')
    .factory('Errors', ['$resource', function ($resource) {
        return $resource('ThreatKB/errors/:id', {}, {
            'query': {method: 'GET', isArray: true},
            'get': {method: 'GET'},
            'update': {method: 'PUT'}
        });
    }]);
