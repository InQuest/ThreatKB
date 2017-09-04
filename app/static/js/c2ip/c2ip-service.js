'use strict';

angular.module('ThreatKB')
    .factory('C2ip', ['$resource', function ($resource) {
        return $resource('ThreatKB/c2ips/:id', {}, {
            'query': {method: 'GET', isArray: true},
            'get': {method: 'GET'},
            'update': {method: 'PUT'}
        });
    }]);
