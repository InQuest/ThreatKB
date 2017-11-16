'use strict';

angular.module('ThreatKB')
    .factory('Tags', ['$resource', '$q', '$timeout', '$http', function ($resource, $q, $timeout, $http) {

        var tags_resource = $resource('ThreatKB/tags/:id', {}, {
            'query': {method: 'GET', isArray: true},
            'get': {method: 'GET'},
            'update': {method: 'PUT'}
        });

        function loadTags(query) {
            return $http.get('/ThreatKB/tags', {cache: false}).then(function (response) {
                var tags = response.data;
                return tags.filter(function (tag) {
                    return tag.text.toLowerCase().indexOf(query.toLowerCase()) !== -1;
                });
            }, function (error) {
                return $q.reject(error.data);
            });
        }

        return {
            resource: tags_resource,
            loadTags: loadTags
        };
    }]);
