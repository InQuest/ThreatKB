angular.module('ThreatKB')
    .factory('Countries', ['$resource',
            function ($resource) {
                return $resource('/ThreatKB/countries', {}, {
                    'query': {method: 'GET', isArray: true}
                });
            }
        ]
    );
