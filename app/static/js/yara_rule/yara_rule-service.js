'use strict';

angular.module('ThreatKB')
    .factory('Yara_rule', ['$resource', '$http', '$q', function ($resource, $http, $q) {

        function copySignatures(ids) {
            return $http.post('/ThreatKB/yara_rules/copy', {
                copy: ids
            }).then(function (success) {
                    if (success.status === 200 && success.data) {
                        return success.data;
                    }
                }, function (error) {
                    return $q.reject(error.data);
                }
            );
        }

        function merge_signature(merge_from_id, merge_to_id) {
            return $http.post('/ThreatKB/yara_rules/merge_signatures', {
                merge_from_id: merge_from_id,
                merge_to_id: merge_to_id
            }).then(function (success) {
                    if (success.status === 200 && success.data) {
                        return success.data;
                    } else {
                        //TODO
                    }
                }, function (error) {
                    return $q.reject(error.data);
                }
            );
        }

        function updateBatch(batch) {
            return $http.put('/ThreatKB/yara_rules/batch/edit', {
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

        function activateRule(rule_id) {
            return $http.put('/ThreatKB/yara_rules/activate/' + rule_id).then(function (success) {
                    if (success.status === 200) {
                        return success.data;
                    }
                }, function (error) {
                    return $q.reject(error.data);
                }
            );
        }

        function delete_all_inactive() {
            return $http.put('/ThreatKB/yara_rules/delete_all_inactive').then(function (success) {
                    if (success.status === 200) {
                        return success.data;
                    }
                }, function (error) {
                    return $q.reject(error.data);
                }
            );
        }

        function deleteBatch(batch) {
            return $http.put('/ThreatKB/yara_rules/batch/delete', {
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

        function getSignatureFromRevision(sig_id, revision) {
            return $http.get('/ThreatKB/yara_rules/' + sig_id + '/revision/' + revision)
                .then(function (success) {
                    if (success.status === 200) {
                        return success.data;
                    }
                }, function (error) {
                    return $q.reject(error.data);
                }
            );
        }

        function deleteFile(file) {
            return $http.delete('/ThreatKB/files/' + file.id).then(function (success) {
                    if (success.status === 200) {
                        return success.data;
                    }
                }, function (error) {
                    return $q.reject(error.data);
                }
            );
        }

        return {
            resource: $resource('ThreatKB/yara_rules/:id', {}, {
                'query': {method: 'GET', isArray: true},
                'get': {method: 'GET'},
                'update': {method: 'PUT'}
            }),
            copySignatures: copySignatures,
            merge_signature: merge_signature,
            updateBatch: updateBatch,
            deleteBatch: deleteBatch,
            getSignatureFromRevision: getSignatureFromRevision,
            activateRule: activateRule,
            delete_all_inactive: delete_all_inactive,
            deleteFile: deleteFile
        };
    }]);

