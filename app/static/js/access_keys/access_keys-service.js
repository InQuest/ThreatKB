'use strict';

angular.module('ThreatKB')
    .factory('AccessKeys', ['$resource', '$http', function ($resource, $http) {

        var access_keys_resource = $resource('/ThreatKB/access_keys/:id', {}, {
            'query': {method: 'GET', isArray: true},
            'get': {method: 'GET'},
            'update': {method: 'PUT'}
        });

        function getActiveInactiveCount() {
            return $http.get('/ThreatKB/access_keys/count', {cache: false})
                .then(function (response) {
                    return response;
                }, function (error) {
                });
        }

        return {
            resource: access_keys_resource,
            getActiveInactiveCount: getActiveInactiveCount
        };
    }]);
