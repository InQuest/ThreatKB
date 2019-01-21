'use strict';

angular.module('ThreatKB')
    .factory('Task', ['$resource', '$q', '$http', function ($resource, $q, $http) {

        function updateBatch(batch) {
            return $http.put('/ThreatKB/tasks/batch', {
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
            resource: $resource('ThreatKB/tasks/:id', {}, {
                'query': {method: 'GET', isArray: true},
                'get': {method: 'GET'},
                'update': {method: 'PUT'}
            }),
            updateBatch: updateBatch
        };
    }]);
