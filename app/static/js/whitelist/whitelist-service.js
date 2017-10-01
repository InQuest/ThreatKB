'use strict';

angular.module('ThreatKB')
    .factory('Whitelist', ['$resource', function ($resource) {
        return $resource('ThreatKB/whitelist/:id', {}, {
            'query': {method: 'GET', isArray: true},
            'get': {method: 'GET'},
            'update': {method: 'PUT'}
        });
    }]);
