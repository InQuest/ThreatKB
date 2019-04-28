'use strict';

angular.module('ThreatKB')
    .factory('Macros', ['$resource', function ($resource) {
        return $resource('ThreatKB/macros/:tag', {}, {
            'query': {method: 'GET', isArray: true},
            'get': {method: 'GET'},
            'update': {method: 'PUT'}
        });
    }]);
