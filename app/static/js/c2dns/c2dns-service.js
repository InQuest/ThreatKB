'use strict';

angular.module('ThreatKB')
    .factory('C2dns', ['$resource', function ($resource) {
        return $resource('ThreatKB/c2dns/:id', {}, {
            'query': {method: 'GET', isArray: true},
            'get': {method: 'GET'},
            'update': {method: 'PUT'}
        });
    }]);
