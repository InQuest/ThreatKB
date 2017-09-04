'use strict';

angular.module('InquestKB')
    .factory('Release', ['$resource', '$q', '$timeout', '$http', function ($resource, $q, $timeout, $http) {

        var release_resource = $resource('InquestKB/releases/:id', {}, {
            'query': {method: 'GET', isArray: true},
            'get': {method: 'GET'}
        });

        function generate_release_notes(id) {
            return $http.get('/InquestKB/releases/' + id + '/release_notes', {cache: false}).then(function (response) {
                return response;
            }, function (error) {
                return $q.reject(error.data);
            })
        };

        function generate_signature_export(id) {
            return $http.get('/InquestKB/releases/' + id + '/signature_export', {
                cache: false,
                responseType: "arraybuffer"
            }).then(function (response) {
                return response;
            }, function (error) {
                return $q.reject(error.data);
            })
        };

        return {
            resource: release_resource,
            generate_release_notes: generate_release_notes,
            generate_signature_export: generate_signature_export
        };
    }]);
