'use strict';

angular.module('InquestKB')
    .factory('Yara_rule', ['$resource', function ($resource) {
        return $resource('InquestKB/yara_rules/:id', {}, {
            'query': {method: 'GET', isArray: true},
            'get': {method: 'GET'},
            'update': {method: 'PUT'}
        });
    }]);
