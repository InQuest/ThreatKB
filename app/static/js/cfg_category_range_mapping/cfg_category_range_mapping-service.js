'use strict';

angular.module('InquestKB')
    .factory('CfgCategoryRangeMapping', ['$resource', function ($resource) {
        return $resource('InquestKB/cfg_category_range_mapping/:id', {}, {
            'query': {method: 'GET', isArray: true},
            'get': {method: 'GET'},
            'update': {method: 'PUT'}
        });
    }]);
