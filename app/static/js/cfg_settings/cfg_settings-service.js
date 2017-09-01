'use strict';

angular.module('ThreatKB')
    .factory('Cfg_settings', ['$resource', function ($resource) {
        return $resource('ThreatKB/cfg_settings/:key', {}, {
            'query': {method: 'GET', isArray: true},
            'get': {method: 'GET'},
            'update': {method: 'PUT'}
        });
    }]);
