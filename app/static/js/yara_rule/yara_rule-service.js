'use strict';

angular.module('ThreatKB')
    .factory('Yara_rule', ['$resource', function ($resource) {
        return $resource('ThreatKB/yara_rules/:id', {}, {
            'query': {method: 'GET', isArray: true},
            'get': {method: 'GET'},
            'update': {method: 'PUT'}
        });
    }]);
