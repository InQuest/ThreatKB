'use strict';

angular.module('ThreatKB')
    .factory('Tests', ['$resource', '$q', '$http', function ($resource, $q, $http) {

        return {
            resource: $resource('ThreatKB/tests/:id', {}, {
                'query': {method: 'GET', isArray: true},
                'get': {method: 'GET'},
                'update': {method: 'PUT'}
            })
        };
    }]);
