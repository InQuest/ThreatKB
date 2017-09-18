'use strict';

angular.module('ThreatKB')
    .factory('Task', ['$resource', function ($resource) {
        return $resource('ThreatKB/tasks/:id', {}, {
            'query': {method: 'GET', isArray: true},
            'get': {method: 'GET'},
            'update': {method: 'PUT'}
        });
    }]);
