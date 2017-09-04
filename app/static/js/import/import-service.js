angular.module('InquestKB').factory('Import',
    ['$q', '$timeout', '$http',
        function ($q, $timeout, $http) {


            // return available functions for use in controllers
            return ({
                import_artifacts: import_artifacts,
                commit_artifacts: commit_artifacts
            });

            function import_artifacts(import_text, autocommit, shared_reference, shared_state) {
                // send a post request to the server
                return $http.post('/InquestKB/import', {
                    import_text: import_text,
                    autocommit: autocommit,
                    shared_reference: shared_reference,
                    shared_state: shared_state
                })
                    .then(function (success) {
                            if (success.status === 200 && success.data.artifacts) {
                                return success.data.artifacts;
                            } else {
                                //TODO
                            }
                        }, function (error) {
                        return $q.reject(error.data);
                        }
                    );

            }

            function commit_artifacts(artifacts, shared_reference, shared_state) {
                // send a post request to the server
                return $http.post('/InquestKB/import/commit', {
                    artifacts: artifacts,
                    shared_reference: shared_reference,
                    shared_state: shared_state
                })
                    .then(function (success) {
                        if (success.status === 201 && success.data.artifacts) {
                            return success.data.artifacts;
                        } else {
                            //TODO
                        }
                    }, function (error) {
                        return $q.reject(error.data);
                    });

            }


        }]);
