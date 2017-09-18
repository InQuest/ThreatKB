'use strict';

angular.module('ThreatKB')
    .factory('CfgCategoryRangeMapping', ['$resource', function ($resource) {
        return $resource('ThreatKB/cfg_category_range_mapping/:id', {}, {
            'query': {method: 'GET', isArray: true},
            'get': {method: 'GET'},
            'update': {method: 'PUT'}
        });
    }]);
