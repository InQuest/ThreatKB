angular.module('ThreatKB')
    .controller('AuthController', ['$scope', '$location', 'AuthService', 'Cfg_settings',
        function ($scope, $location, AuthService, Cfg_settings) {
            $scope.isLoggedIn = AuthService.isLoggedIn;
            $scope.isAdmin = AuthService.isAdmin;
            $scope.nav_image = Cfg_settings.get({key: "NAV_IMAGE"});

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
