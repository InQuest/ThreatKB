angular.module('ThreatKB').factory('AuthService',
    ['$q', '$timeout', '$http',
        function ($q, $timeout, $http) {

            // create user variable
            var user = null;

            // return available functions for use in controllers
            return ({
                isLoggedIn: isLoggedIn,
                login: login,
                logout: logout,
                register: register,
                getUserStatus: getUserStatus
            });

            function isLoggedIn() {
                if (user) {
                    return true;
                } else {
                    return false;
                }
            }

            function login(email, password) {
                // create a new instance of deferred
                var deferred = $q.defer();

                // send a post request to the server
                $http.post('/ThreatKB/login', {email: email, password: password})
                    .then(function(success) {
                        if (success.status === 200 && success.data.result) {
                            user = true;
                            deferred.resolve();
                        } else {
                            user = false;
                            deferred.reject();
                        }
                    },function(error) {
                        user = false;
                        deferred.reject();
                    });

                // return promise object
                return deferred.promise;

            }

            function logout() {

                // create a new instance of deferred
                var deferred = $q.defer();

                // send a get request to the server
                $http.get('/ThreatKB/logout')
                    // handle success
                    .then(function(success) {
                        user = false;
                        deferred.resolve();
                    },
                    // handle error
                    function(error) {
                        user = false;
                        deferred.reject();
                    });

                // return promise object
                return deferred.promise;

            }

            function register(email, password) {
                // create a new instance of deferred
                var deferred = $q.defer();

                // send a post request to the server
                $http.post('/ThreatKB/register', {email: email, password: password})
                    // handle success
                    .then(function(success) {
                        if (success.status === 200 && success.data.result) {
                            deferred.resolve();
                        } else {
                            deferred.reject();
                        }
                    },
                    // handle error
                    function(error) {
                        deferred.reject();
                    });

                // return promise object
                return deferred.promise;
            }

            function getUserStatus() {
                return $http.get('/ThreatKB/status')
                    // handle success
                    .then(function(success) {
                            if (success.status == 200 && success.data.status) {
                            user = true;
                        } else {
                            user = false;
                        }
                    },
                    // handle error
                    function(error) {
                        user = false;
                    });
            }

        }]);
