'use strict';

angular.module('ThreatKB')
    .factory('Release', ['$resource', '$q', '$timeout', '$http', function ($resource, $q, $timeout, $http) {

        var release_resource = $resource('/ThreatKB/releases/:id', {}, {
            'query': {method: 'GET', isArray: true},
            'get': {method: 'GET'}
        });

        function generate_release_notes(id) {
            return $http.get('/ThreatKB/releases/' + id + '/release_notes', {cache: false}).then(function (response) {
                return response;
            }, function (error) {
                return $q.reject(error.data);
            })
        };

        function generate_artifact_export(id) {
            return $http.get('/ThreatKB/releases/' + id + '/artifact_export', {
                cache: false,
                responseType: "arraybuffer"
            }).then(function (response) {
                return response;
            }, function (error) {
                return $q.reject(error.data);
            })
        };

        function get_latest_releases() {
            return $http.get('/ThreatKB/releases/latest', {
                cache: false,
            }).then(function (response) {
                return response.data;
            }, function (error) {
                return $q.reject(error.data);
            })
        }

        return {
            resource: release_resource,
            get_latest_releases: get_latest_releases,
            generate_release_notes: generate_release_notes,
            generate_artifact_export: generate_artifact_export
        };
    }]);
