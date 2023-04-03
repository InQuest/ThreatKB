'use strict';

angular.module('ThreatKB')
    .factory('Files', ['$resource', function ($resource) {
        return {
            resource: $resource('ThreatKB/files/:id', {}, {
                'query': {method: 'GET', isArray: true},
                'get': {method: 'GET'},
                'update': {method: 'PUT'}
            }),
            ENTITY_MAPPING: {SIGNATURE: 1}
        };
    }]);
