'use strict';

angular.module('InquestKB')
    .factory('Cfg_reference_text_templates', ['$resource', function ($resource) {
        return $resource('InquestKB/cfg_reference_text_templates/:id', {}, {
            'query': {method: 'GET', isArray: true},
            'get': {method: 'GET'},
            'update': {method: 'PUT'}
        });
    }]);
