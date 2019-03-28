angular.module('ThreatKB')
    .controller('AuthController', ['$scope', '$location', 'AuthService', 'Cfg_settings', 'hotkeys', 'C2dns', 'C2ip', 'Yara_rule', 'Task',
        function ($scope, $location, AuthService, Cfg_settings, hotkeys, C2dns, C2ip, Yara_rule, Task) {
            $scope.isLoggedIn = AuthService.isLoggedIn;
            $scope.isAdmin = AuthService.isAdmin;
            $scope.user = AuthService.user;
            $scope.nav_image = Cfg_settings.get({key: "NAV_IMAGE"});

            if ($scope.isLoggedIn()) {
                $location.path("/");
            }

            $scope.search_artifacts = [];

            $scope.getPermalink = function (url) {
                return $location.absUrl().split("/").slice(0, 4).join("/") + url;
            };

            $scope.select_artifact = function (selected) {
                $location.url(selected.url);
            };

            hotkeys.bindTo($scope)
                .add({
                    combo: 'ctrl+j',
                    description: 'Search',
                    allowIn: ['INPUT', 'SELECT', 'TEXTAREA'],
                    callback: function () {
                        //$document.find("input#focusser-0")[0].focus();
                        $scope.$broadcast('search_focus');
                    }
                });

            $scope.refresh_search = function (search) {
                if (!search) {
                    return;
                }

                $scope.search_artifacts = [];

                var dns_results = C2dns.resource.query({
                    searches: {domain_name: search},
                    exclude_totals: true,
                    include_metadata: false
                });
                dns_results.$promise.then(function (results) {
                    results.forEach(function (c2dns) {
                        $scope.search_artifacts.push({
                            name: c2dns.domain_name,
                            id: c2dns.id,
                            type: "c2dns",
                            url: "/c2dns/" + c2dns.id
                        });
                    });
                }, function (error) {
                    console.log(error);
                });

                var yara_results = Yara_rule.resource.query({
                    searches: {
                        name: search,
                        description: search,
                        references: search,
                        strings: search,
                        condition: search
                    },
                    exclude_totals: true,
                    include_metadata: false,
                    include_yara_string: false,
                    short: 1,
                    operator: "or"
                });
                yara_results.$promise.then(function (results) {
                    results.forEach(function (yara_rule) {
                        $scope.search_artifacts.push({
                            name: yara_rule.name,
                            id: yara_rule.id,
                            type: "yara_rule",
                            url: "/yara_rules/" + yara_rule.id
                        });
                    });
                }, function (error) {
                    console.log(error);
                });

                var ip_results = C2ip.resource.query({
                    searches: {ip: search},
                    exclude_totals: true,
                    include_metadata: false
                });
                ip_results.$promise.then(function (results) {
                    results.forEach(function (c2ip) {
                        $scope.search_artifacts.push({
                            name: c2ip.ip,
                            id: c2ip.id,
                            type: "c2ip",
                            url: "/c2ips/" + c2ip.id
                        });
                    });

                }, function (error) {
                    console.log(error);
                });

                var task_results = Task.resource.query({
                    searches: {title: search},
                    exclude_totals: true,
                    include_metadata: false
                });
                task_results.$promise.then(function (results) {
                    results.forEach(function (task) {
                        $scope.search_artifacts.push({
                            name: task.title,
                            id: task.id,
                            type: "task",
                            url: "/tasks/" + task.id
                        });
                    });

                }, function (error) {
                    console.log(error);
                });

            };

            $scope.login = function () {
                // initial values
                $scope.error = false;
                $scope.disabled = true;

                // call login from service
                AuthService.login($scope.login_form.email, $scope.login_form.password)
                    .then(function () {
                        $location.path('/');
                        $scope.disabled = false;
                        $scope.loginForm = {};
                    })
                    .catch(function () {
                        $scope.error = true;
                        $scope.errorMessage = "Invalid username and/or password";
                        $scope.disabled = false;
                        $scope.login_form = {};
                    });
            };

            $scope.logout = function () {
                // call logout from service
                AuthService.logout()
                    .then(function () {
                        $location.path('/login');
                    });

            };

        }])
    .controller('UsersController', ['$scope', '$uibModal', 'resolvedUsers', 'UserService',
        function ($scope, $uibModal, resolvedUsers, UserService) {
            $scope.users = resolvedUsers;
            $scope.user = {};
            $scope.user.passwordConfirm = "";

            $scope.customSearch = function(actual, expected) {
                if (expected.length < 3) {
                    return true;
                } else if (typeof actual !== "object") {
                    return actual.toString().toLowerCase().indexOf(expected.toString().toLowerCase()) !== -1;
                } else {
                    return false;
                }
            };

            $scope.create = function () {
                $scope.clear();
                $scope.open();
            };

            $scope.update = function (id) {
                $scope.user = UserService.get({id: id});
                $scope.users = UserService.query({include_inactive: 1});
                $scope.open(id);
            };

            $scope.save = function (id) {
                if (id) {
                    UserService.update({id: id}, $scope.user, function () {
                        $scope.users = UserService.query({include_inactive: 1});
                    });
                } else {
                    UserService.save($scope.user, function () {
                        $scope.users = UserService.query({include_inactive: 1});
                    });
                }
            };

            $scope.clear = function () {
                $scope.user = {
                    "email": "",
                    "password": "",
                    "passwordConfirm": "",
                    "admin": false,
                    "active": true,
                    "registered_on": ""
                };
            };

            $scope.delete = function (id) {
                UserService.delete({id: id}, function () {
                    $scope.users = UserService.query({include_inactive: 1});
                });
            };

            $scope.open = function (id) {
                var userSave = $uibModal.open({
                    templateUrl: 'users-save.html',
                    controller: 'UsersSaveController',
                    resolve: {
                        user: function () {
                            return $scope.user;
                        }
                    }
                });

                userSave.result.then(function (user) {
                    $scope.user = user;
                    $scope.save(id);
                });
            };
        }])
    .controller('UsersSaveController', ['$scope', '$http', '$uibModalInstance', 'user',
        function ($scope, $http, $uibModalInstance, user) {
            $scope.user = user;
            $scope.user.passwordConfirm = "";

            $scope.ok = function () {
                $uibModalInstance.close($scope.user);
            };

            $scope.cancel = function () {
                $uibModalInstance.dismiss('cancel');
            };

            $scope.setAdmin = function (val) {
                $scope.user.admin = val;
            };

            $scope.setActive = function (val) {
                $scope.user.active = val;
            };
        }]);
