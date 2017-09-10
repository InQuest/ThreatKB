// Declare app level module which depends on filters, and services
angular.module('ThreatKB', ['ngResource', 'ngRoute', 'ui.bootstrap', 'ngSanitize', 'ui.select', 'ngTagsInput', 'angular-growl', 'ngFileSaver', 'ngPassword', 'ngMessages', 'blockUI',
    'angular-toArrayFilter', 'ui.codemirror', 'ngFileUpload', 'ngFileSaver', 'ngPassword', 'ngMessages', 'blockUI'])
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
            .when('/cfg_category_range_mapping', {
                templateUrl: 'views/cfg_category_range_mapping/cfg_category_range_mapping.html',
                controller: 'CfgCategoryRangeMappingController',
                access: {restricted: true},
                resolve: {
                    resolvedCfgCategoryRangeMapping: ['CfgCategoryRangeMapping', function (CfgCategoryRangeMapping) {
                        return CfgCategoryRangeMapping.query();
                    }]
                }
            })
            .when('/cfg_settings', {
                templateUrl: 'views/cfg_settings/cfg_settings.html',
                controller: 'Cfg_settingsController',
                access: {restricted: true},
                resolve: {
                    resolvedCfg_settings: ['Cfg_settings', function (Cfg_settings) {
                        return Cfg_settings.query();
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
            .when('/files', {
                templateUrl: 'views/files/files.html',
                controller: 'FilesController',
                access: {restricted: true},
                resolve: {
                    resolvedFiles: ['Files', function (Files) {
                        return Files.resource.query();
                    }]
                }
            })
            .when('/users', {
                templateUrl: 'views/users/users.html',
                controller: 'UsersController',
                access: {restricted: true},
                resolve: {
                    resolvedUsers: ['UserService', function (UserService) {
                        return UserService.query({include_inactive: 1});
                    }]
                }
            })
            .when('/import', {
                templateUrl: 'views/import/import.html',
                controller: 'ImportController',
                access: {restricted: true}
            })
            .when('/releases', {
                templateUrl: 'views/releases/releases.html',
                controller: 'ReleaseController',
                access: {restricted: true},
                resolve: {
                    resolvedRelease: ['Release', function (Release) {
                        return Release.resource.query();
                    }]
                }
            })
            .otherwise({
                redirectTo: '/'
            });
    }])
;

angular.module('ThreatKB').run(function ($rootScope, $location, AuthService) {

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

angular.module('ThreatKB').directive('ngConfirmClick', [
    function () {
        return {
            link: function (scope, element, attr) {
                var msg = attr.ngConfirmClick || "Are you sure?";
                var clickAction = attr.confirmedClick;
                element.bind('click', function (event) {
                    if (window.confirm(msg)) {
                        scope.$eval(clickAction)
                    }
                });
            }
        };
    }])
