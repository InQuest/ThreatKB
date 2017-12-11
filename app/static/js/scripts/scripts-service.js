'use strict';

angular.module('ThreatKB')
    .factory('Script', ['$resource', '$http', '$q', function ($resource, $http, $q) {

        function run_script(script_id, arguments_, highlight_lines_matching) {
            return $http.post('/ThreatKB/scripts/run/' + script_id, {
                highlight_lines_matching: highlight_lines_matching,
                arguments: arguments_
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
            resource: $resource('ThreatKB/scripts/:id', {}, {
                'query': {method: 'GET', isArray: true},
                'get': {method: 'GET'},
                'update': {method: 'PUT'}
            }), run_script: run_script
        };
    }]);
