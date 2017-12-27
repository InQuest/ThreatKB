'use strict';

angular.module('ThreatKB')
    .factory('Metadata', ['$resource', function ($resource) {
        return $resource('ThreatKB/metadata/:key', {}, {
            'query': {method: 'GET', isArray: true},
            'get': {method: 'GET'},
            'update': {method: 'PUT'}
        });
    }]);
