'use strict';

angular.module('ThreatKB')
    .factory('Task', ['$resource', '$q', '$http', function ($resource, $q, $http) {
        var task_resource = $resource('ThreatKB/tasks/:id', {}, {
            'query': {method: 'GET', isArray: true},
            'get': {method: 'GET'},
            'update': {method: 'PUT'}
        });

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
            resource: task_resource,
            updateBatch: updateBatch
        };
    }]);
