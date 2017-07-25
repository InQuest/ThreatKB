// Declare app level module which depends on filters, and services
angular.module('InquestKB', ['ngResource', 'ngRoute', 'ui.bootstrap', 'ui.date'])
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
            .when('/yara_rules', {
                templateUrl: 'views/yara_rule/yara_rules.html',
                controller: 'Yara_ruleController',
                access: {restricted: true},
                resolve: {
                    resolvedYara_rule: ['Yara_rule', function (Yara_rule) {
                        return Yara_rule.query();
                    }]
                }
            }).otherwise({
            redirectTo: '/'
        });

    }]);

angular.module('InquestKB').run(function ($rootScope, $location, AuthService) {

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
