'use strict';

angular.module('ThreatKB')
    .factory('Files', ['$resource', '$q', '$http', function ($resource, $q, $http) {

        function deleteBatch(batch) {
            return $http.put('/ThreatKB/files/batch/delete', {
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
            resource: $resource('ThreatKB/files/:id', {}, {
                'query': {method: 'GET', isArray: true},
                'get': {method: 'GET'},
                'update': {method: 'PUT'}
            }),
            deleteBatch: deleteBatch,
            ENTITY_MAPPING: {SIGNATURE: 1}
        };
    }]);
