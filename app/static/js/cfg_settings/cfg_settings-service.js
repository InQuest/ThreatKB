'use strict';

angular.module('InquestKB')
    .factory('Cfg_settings', ['$resource', function ($resource) {
        return $resource('InquestKB/cfg_settings/:key', {}, {
            'query': {method: 'GET', isArray: true},
            'get': {method: 'GET'},
            'update': {method: 'PUT'}
        });
    }]);
