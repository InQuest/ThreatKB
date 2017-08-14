// Declare app level module which depends on filters, and services
angular.module('InquestKB', ['ngResource', 'ngRoute', 'ui.bootstrap', 'ngSanitize', 'ui.select', 'ngTagsInput', 'angular-growl',
    'angular-toArrayFilter', 'ui.codemirror', 'ngFileUpload'])
    .config(['$routeProvider', function ($routeProvider) {
        $routeProvider
            .when('/', {
                templateUrl: 'views/home.html',
                //controller: 'HomeController',
                access: {restricted: true}
            })
            .when('/login', {
                templateUrl: 'views/login.html',
                controller: 'AuthController',
                access: {restricted: false}
            })
            .when('/logout', {
                controller: 'AuthController',
                access: {restricted: true}
            })
            .when('/c2dns', {
                templateUrl: 'views/c2dns/c2dns.html',
                controller: 'C2dnsController',
                access: {restricted: true},
                resolve: {
                    resolvedC2dns: ['C2dns', function (C2dns) {
                        return C2dns.query();
                    }]
                }
            })
            .when('/c2ips', {
                templateUrl: 'views/c2ip/c2ips.html',
                controller: 'C2ipController',
                access: {restricted: true},
                resolve: {
                    resolvedC2ip: ['C2ip', function (C2ip) {
                        return C2ip.query();
                    }]
                }
            })
            .when('/cfg_reference_text_templates', {
                templateUrl: 'views/cfg_reference_text_templates/cfg_reference_text_templates.html',
                controller: 'Cfg_reference_text_templatesController',
                access: {restricted: true},
                resolve: {
                    resolvedCfg_reference_text_templates: ['Cfg_reference_text_templates', function (Cfg_reference_text_templates) {
                        return Cfg_reference_text_templates.query();
                    }]
                }
            })
            .when('/cfg_states', {
                templateUrl: 'views/cfg_states/cfg_states.html',
                controller: 'Cfg_statesController',

                access: {restricted: true},
                resolve: {
                    resolvedCfg_states: ['Cfg_states', function (Cfg_states) {
                        return Cfg_states.query();
                    }]
                }
            })
            .when('/tags', {
                templateUrl: 'views/tags/tags.html',
                controller: 'TagsController',
                access: {restricted: true},
                resolve: {
                    resolvedTags: ['Tags', function (Tags) {
                        return Tags.query();
                    }]
                }
            })
            .when('/yara_rules', {
                templateUrl: 'views/yara_rule/yara_rules.html',
                controller: 'Yara_ruleController',
                access: {restricted: true},
                resolve: {
                    resolvedYara_rule: ['Yara_rule', function (Yara_rule) {
                        return Yara_rule.query();
                    }]
                }
            })
            .when('/import', {
                templateUrl: 'views/import/import.html',
                controller: 'ImportController',
                access: {restricted: true}
            }).otherwise({
            redirectTo: '/'
        });

    }])
;

angular.module('InquestKB').run(function ($rootScope, $location, AuthService) {

    $rootScope.pretty_date = function prettyDate(time) {
        var date = new Date((time || "").replace(/-/g, "/").replace(/[TZ]/g, " ")),
            diff = (((new Date()).getTime() - date.getTime()) / 1000),
            day_diff = Math.floor(diff / 86400);

        if (isNaN(day_diff) || day_diff < 0 || day_diff >= 31)
            return;

        return day_diff == 0 && (
            diff < 60 && "just now" ||
            diff < 120 && "1 minute ago" ||
            diff < 3600 && Math.floor(diff / 60) + " minutes ago" ||
            diff < 7200 && "1 hour ago" ||
            diff < 86400 && Math.floor(diff / 3600) + " hours ago") ||
            day_diff == 1 && "Yesterday" ||
            day_diff < 7 && day_diff + " days ago" ||
            day_diff < 31 && Math.ceil(day_diff / 7) + " weeks ago";
    };

    // Register listener to watch route changes.
    $rootScope.$on('$routeChangeStart', function (event, next, current) {
        AuthService.getUserStatus().then(function () {
                if (next.access.restricted && !AuthService.isLoggedIn()) {
                    $location.path('/login');
                    $route.reload();
                }
            }
        )
    });

});
