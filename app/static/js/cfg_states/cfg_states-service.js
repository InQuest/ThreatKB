'use strict';

angular.module('InquestKB')
    .factory('Cfg_states', ['$resource', function ($resource) {
        return $resource('InquestKB/cfg_states/:id', {}, {
            'query': {method: 'GET', isArray: true},
            'get': {method: 'GET'},
            'update': {method: 'PUT'}
        });
    }]);
