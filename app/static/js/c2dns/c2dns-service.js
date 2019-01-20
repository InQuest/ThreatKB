'use strict';

angular.module('ThreatKB')
    .factory('C2dns', ['$resource', '$q', '$http', function ($resource, $q, $http) {
        var c2dns_resource = $resource('ThreatKB/c2dns/:id', {}, {
            'query': {method: 'GET', isArray: true},
            'get': {method: 'GET'},
            'update': {method: 'PUT'}
        });

        function updateBatch(batch) {
            return $http.put('/ThreatKB/c2dns/batch', {
                batch: batch
            }).then(function (success) {
                    if (success.status === 200) {
                        return success.data;
                    }
                }, function (error) {
                    return $q.reject(error.data);
                }
            );
        }

        return {
            resource: c2dns_resource,
            updateBatch: updateBatch
        };
    }]);
