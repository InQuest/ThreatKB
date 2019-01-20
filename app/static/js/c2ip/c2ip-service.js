'use strict';

angular.module('ThreatKB')
    .factory('C2ip', ['$resource', '$q', '$http', function ($resource, $q, $http) {
        var c2ip_resource = $resource('ThreatKB/c2ips/:id', {}, {
            'query': {method: 'GET', isArray: true},
            'get': {method: 'GET'},
            'update': {method: 'PUT'}
        });

        function updateBatch(batch) {
            return $http.put('/ThreatKB/c2ips/batch', {
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
            resource: c2ip_resource,
            updateBatch: updateBatch
        };
    }]);
