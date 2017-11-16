'use strict';

angular.module('ThreatKB')
    .factory('Yara_rule', ['$resource', '$http', '$q', function ($resource, $http, $q) {

        function merge_signature(merge_from_id, merge_to_id) {
            return $http.post('/ThreatKB/yara_rules/merge_signatures', {
                merge_from_id: merge_from_id,
                merge_to_id: merge_to_id
            })
                .then(function (success) {
                        if (success.status === 200 && success.data) {
                            return success.data;
                        } else {
                            //TODO
                        }
                    }, function (error) {
                        return $q.reject(error.data);
                    }
                );
        };

        return {
            resource: $resource('ThreatKB/yara_rules/:id', {}, {
                'query': {method: 'GET', isArray: true},
                'get': {method: 'GET'},
                'update': {method: 'PUT'}
            }), merge_signature: merge_signature
        };
    }]);
