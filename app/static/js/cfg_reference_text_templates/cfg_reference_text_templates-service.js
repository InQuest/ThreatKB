'use strict';

angular.module('ThreatKB')
    .factory('Cfg_reference_text_templates', ['$resource', function ($resource) {
        return $resource('ThreatKB/cfg_reference_text_templates/:id', {}, {
            'query': {method: 'GET', isArray: true},
            'get': {method: 'GET'},
            'update': {method: 'PUT'}
        });
    }]);
