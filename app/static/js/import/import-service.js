angular.module('ThreatKB').factory('Import',
    ['$q', '$timeout', '$http',
        function ($q, $timeout, $http) {


            // return available functions for use in controllers
            return ({
                import_artifacts: import_artifacts,
                commit_artifacts: commit_artifacts
            });

            function import_artifacts(import_text, autocommit, resurrect_retired_artifacts, shared_reference, shared_description, shared_state, shared_owner, extract_ip, extract_dns, extract_signature, metadata_field_mapping) {
                // send a post request to the server
                return $http.post('/ThreatKB/import', {
                    import_text: import_text,
                    autocommit: autocommit,
                    resurrect_retired_artifacts: resurrect_retired_artifacts,
                    shared_reference: shared_reference,
                    shared_description: shared_description,
                    shared_state: shared_state,
                    shared_owner: shared_owner,
                    extract_ip: extract_ip,
                    extract_dns: extract_dns,
                    extract_signature: extract_signature,
                    metadata_field_mapping: metadata_field_mapping
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

            function commit_artifacts(artifacts, resurrect_retired_artifacts, shared_reference, shared_description, shared_state, shared_owner, extract_ip, extract_dns, extract_signature, metadata_field_mapping) {
                // send a post request to the server
                return $http.post('/ThreatKB/import/commit', {
                    artifacts: artifacts,
                    resurrect_retired_artifacts: resurrect_retired_artifacts,
                    shared_reference: shared_reference,
                    shared_description: shared_description,
                    shared_state: shared_state,
                    shared_owner: shared_owner,
                    extract_ip: extract_ip,
                    extract_dns: extract_dns,
                    extract_signature: extract_signature,
                    metadata_field_mapping: metadata_field_mapping
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
