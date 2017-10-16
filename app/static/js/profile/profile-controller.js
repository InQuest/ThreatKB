angular.module('ThreatKB')
    .controller('ProfileController', ['$scope', '$route', 'AuthService', 'UserService', 'growl', 'Upload', '$timeout',
        function ($scope, $route, AuthService, UserService, growl, Upload, $timeout) {

            $scope.current_user = null;
            $scope.old_password = null;
            $scope.new_password1 = null;
            $scope.new_password2 = null;

            AuthService.getMe().then(
                function (data) {
                    $scope.current_user = data;
                }, function (error) {
                    //pass
                }
            )

            $scope.uploadFiles = function (file, errFiles) {
                $scope.f = file;
                $scope.errFile = errFiles && errFiles[0];
                if (file) {
                    file.upload = Upload.upload({
                        url: '/ThreatKB/users/me/picture',
                        data: {file: file}
                    });

                    file.upload.then(function (response) {
                        $timeout(function () {
                            file.result = response.data;
                        });
                        growl.info("Successfully updated your picture. Reloading the page.", {
                            ttl: 3000,
                            disableCountDown: true
                        });
                        $route.reload();
                    }, function (response) {
                        if (response.status > 0)
                            $scope.errorMsg = response.status + ': ' + response.data;
                    }, function (evt) {
                        file.progress = Math.min(100, parseInt(100.0 *
                            evt.loaded / evt.total));
                    });
                }
            }

            $scope.password_form_invalid = function () {
                return $scope.old_password && $scope.old_password.length > 0 &&
                    $scope.new_password1 && $scope.new_password2 &&
                    $scope.new_password1.length > 0 && $scope.new_password2.length > 0 &&
                    $scope.new_password1 === $scope.new_password2;
            }

            $scope.update_password = function () {
                AuthService.changePassword($scope.old_password, $scope.new_password1, $scope.new_password2)
                    .then(function (data) {
                        growl.info("Successfully changed your password.", {ttl: 3000});
                    }, function (error) {
                        growl.error(error);
                    })
            };

            $scope.update_profile = function () {
                UserService.update({id: $scope.current_user.id}, $scope.current_user).$promise.then(function (success) {
                    growl.info("Successfully changed your profile.", {ttl: 3000});
                }, function (error) {
                    growl.error(error, {ttl: -1});
                });
            };

        }]);
