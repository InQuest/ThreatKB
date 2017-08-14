angular.module('InquestKB')
    .factory('Files', ['$resource', function ($resource) {
        return {
            resource: $resource('InquestKB/files/:id', {}, {
                'query': {method: 'GET', isArray: true},
                'get': {method: 'GET'}
            }),
            ENTITY_MAPPING: {SIGNATURE: 1}
        };
    }]);
