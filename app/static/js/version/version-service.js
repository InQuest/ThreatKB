'use strict';

angular.module('ThreatKB')
    .factory('Version', ['$resource', '$http', '$q', function ($resource, $http, $q) {

        function get_version() {
            return $http.get('/ThreatKB/version', {
                cache: false,
            }).then(function (response) {
                return response.data;
            }, function (error) {
                return $q.reject(error.data);
            })
        }

        return {
            get_version: get_version
        };
    }]);
