angular.module('ThreatKB')
    .controller('AuthController', ['$scope', '$location', 'AuthService',
        function ($scope, $location, AuthService) {
            $scope.isLoggedIn = AuthService.isLoggedIn;

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
            $scope.users.passwordConfirm = "";

            $scope.create = function () {
                $scope.clear();
                $scope.open();
            };

            $scope.update = function (id) {
                $scope.users = UserService.get({id: id});
                $scope.open(id);
            };

            $scope.save = function (id) {
                if (id) {
                    UserService.update({id: id}, $scope.users, function () {
                        $scope.users = UserService.query();
                    });
                } else {
                    UserService.save($scope.users, function () {
                        $scope.users = UserService.query();
                    });
                }
            };

            $scope.clear = function () {
                $scope.users = {
                    "email": "",
                    "password": "",
                    "passwordConfirm": "",
                    "admin": false,
                    "active": true
                };
            };

            $scope.open = function (id) {
                var userSave = $uibModal.open({
                    templateUrl: 'users-save.html',
                    controller: 'UsersSaveController',
                    resolve: {
                        users: function () {
                            return $scope.users;
                        }
                    }
                });

                userSave.result.then(function (user) {
                    $scope.users = user;
                    $scope.save(id);
                });
            };
        }])
    .controller('UsersSaveController', ['$scope', '$http', '$uibModalInstance', 'users',
        function ($scope, $http, $uibModalInstance, users) {
            $scope.users = users;
            $scope.users.passwordConfirm = "";

            $scope.ok = function () {
                $uibModalInstance.close($scope.users);
            };

            $scope.cancel = function () {
                $uibModalInstance.dismiss('cancel');
            };

            $scope.setAdmin = function (val) {
                $scope.users.admin = val;
            };

            $scope.setActive = function (val) {
                $scope.users.active = val;
            };
        }]);
