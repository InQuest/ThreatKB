angular.module('ThreatKB')
    .factory('Countries', ['$q', '$timeout', '$http',
            function ($q, $timeout, $http) {
                return {
                    getCountries: getCountries
                };

                function getCountries() {
                    return $http.get('/ThreatKB/coutries')
                        .then(function (success) {
                                if (success.status === 200 && success.data) {
                                    return success.data;
                                }
                            }, function (error) {
                                return $q.reject(error.data);
                            }
                        );
                }
            }
        ]
    );
