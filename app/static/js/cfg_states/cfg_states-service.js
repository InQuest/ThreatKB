'use strict';

angular.module('ThreatKB')
    .factory('Cfg_states', ['$resource', function ($resource) {
        return $resource('ThreatKB/cfg_states/:id', {}, {
            'query': {method: 'GET', isArray: true},
            'get': {method: 'GET'},
            'update': {method: 'PUT'}
        });
    }]);
