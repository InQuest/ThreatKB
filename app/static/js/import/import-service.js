angular.module('InquestKB').factory('Import',
    ['$q', '$timeout', '$http',
        function ($q, $timeout, $http) {


            // return available functions for use in controllers
            return ({
                import_artifacts: import_artifacts,
                commit_artifacts: commit_artifacts
            });

            function import_artifacts(import_text, autocommit) {

                autocommit = (typeof autocommit !== 'undefined') ? autocommit : 0;

                // send a post request to the server
                return $http.post('/InquestKB/import', {import_text: import_text, autocommit: autocommit})
                    .then(function (success) {
                            if (success.status === 200 && success.data.artifacts) {
                                return success.data.artifacts;
                            } else {
                                //TODO
                            }
                        }, function (error) {
                            //TODO
                        }
                    );

            }

            function commit_artifacts(artifacts) {
                // send a post request to the server
                return $http.post('/InquestKB/import/commit', {artifacts: artifacts})
                    .then(function (success) {
                        if (success.status === 201 && success.data.artifacts) {
                            return success.data.artifacts;
                        } else {
                            //TODO
                        }
                    }, function (error) {
                        //TODO
                    });

            }


        }]);
