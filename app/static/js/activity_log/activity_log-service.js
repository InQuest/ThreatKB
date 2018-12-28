'use strict';

angular.module('ThreatKB')
    .factory('ActivityLog', ['$resource', function ($resource) {
        return {
            resource: $resource('ThreatKB/activity_log/:id', {}, {
                'query': {method: 'GET', isArray: true}
            }),
            PERMALINK_MAPPING: {
                IP: "c2ips",
                DNS: "c2dns",
                SIGNATURE: "yara_rules",
                TASK: "tasks",
                RELEASE: "releases"
            }
        };
    }]);
