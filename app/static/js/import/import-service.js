angular.module('ThreatKB').factory('Import',
    ['$q', '$timeout', '$http',
        function ($q, $timeout, $http) {


            // return available functions for use in controllers
            return ({
                import_artifacts: import_artifacts,
                commit_artifacts: commit_artifacts
            });

            function import_artifacts(import_text, autocommit, shared_reference, shared_state, shared_owner) {
                // send a post request to the server
                return $http.post('/ThreatKB/import', {
                    import_text: import_text,
                    autocommit: autocommit,
                    shared_reference: shared_reference,
                    shared_state: shared_state,
                    shared_owner: shared_owner
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

            function commit_artifacts(artifacts, shared_reference, shared_state, shared_owner) {
                // send a post request to the server
                return $http.post('/ThreatKB/import/commit', {
                    artifacts: artifacts,
                    shared_reference: shared_reference,
                    shared_state: shared_state,
                    shared_owner: shared_owner
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
