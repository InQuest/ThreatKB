'use strict';

angular.module('ThreatKB')
    .factory('C2ip', ['$resource', '$q', '$http', function ($resource, $q, $http) {

        function updateBatch(batch) {
            return $http.put('/ThreatKB/c2ips/batch/edit', {
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

        function deleteBatch(batch) {
            return $http.put('/ThreatKB/c2ips/batch/delete', {
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

        function activateArtifact(id) {
            return $http.put('/ThreatKB/c2ip/activate/' + id).then(function (success) {
                    if (success.status === 200) {
                        return success.data;
                    }
                }, function (error) {
                    return $q.reject(error.data);
                }
            );
        }

        function delete_all_inactive() {
            return $http.put('/ThreatKB/c2ip/delete_all_inactive').then(function (success) {
                    if (success.status === 200) {
                        return success.data;
                    }
                }, function (error) {
                    return $q.reject(error.data);
                }
            );
        }

        return {
            resource: $resource('ThreatKB/c2ips/:id', {}, {
                'query': {method: 'GET', isArray: true},
                'get': {method: 'GET'},
                'update': {method: 'PUT'}
            }),
            updateBatch: updateBatch,
            deleteBatch: deleteBatch,
            activateArtifact: activateArtifact,
            delete_all_inactive: delete_all_inactive
        };
    }]);
