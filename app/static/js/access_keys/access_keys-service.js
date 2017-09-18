'use strict';

angular.module('ThreatKB')
    .factory('AccessKeys', ['$resource', function ($resource) {
        return $resource('/ThreatKB/access_keys/:id', {}, {
            'query': {method: 'GET', isArray: true},
            'get': {method: 'GET'},
            'update': {method: 'PUT'}
        });
    }]);
