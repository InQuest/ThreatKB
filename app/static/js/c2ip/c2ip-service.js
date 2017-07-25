'use strict';

angular.module('InquestKB')
    .factory('C2ip', ['$resource', function ($resource) {
        return $resource('InquestKB/c2ips/:id', {}, {
            'query': {method: 'GET', isArray: true},
            'get': {method: 'GET'},
            'update': {method: 'PUT'}
        });
    }]);
