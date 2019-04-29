'use strict';

angular.module('ThreatKB')
    .factory('Macros', ['$resource', '$q', '$http', function ($resource, $q, $http) {

        function activate(tag) {
            return $http.put('/ThreatKB/macros/activate/' + tag)
                .then(function (success) {
                        if (success.status === 200) {
                            return success.data;
                        }
                    }, function (error) {
                        return $q.reject(error.data);
                    }
                );
        }

        return {
            resource: $resource('ThreatKB/macros/:tag', {}, {
                'query': {method: 'GET', isArray: true},
                'get': {method: 'GET'},
                'update': {method: 'PUT'}
            }),
            activate: activate
        };
    }]);
