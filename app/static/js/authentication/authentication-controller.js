angular.module('ThreatKB').controller('AuthController',
    ['$scope', '$location', 'AuthService',
        function ($scope, $location, AuthService) {

            $scope.isLoggedIn = AuthService.isLoggedIn;

            $scope.login = function () {

                // initial values
                $scope.error = false;
                $scope.disabled = true;

                // call login from service
                AuthService.login($scope.login_form.email, $scope.login_form.password)
                // handle success
                    .then(function () {
                        $location.path('/');
                        $scope.disabled = false;
                        $scope.loginForm = {};
                    })
                    // handle error
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

        }]);

