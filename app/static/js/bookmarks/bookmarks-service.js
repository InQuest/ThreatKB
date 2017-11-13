angular.module('ThreatKB')
    .factory('Bookmarks', ['$q', '$timeout', '$http',
            function ($q, $timeout, $http) {
                return {
                    getBookmarks: getBookmarks,
                    createBookmark: createBookmark,
                    deleteBookmark: deleteBookmark,
                    ENTITY_MAPPING: {IP: 3, DNS: 2, SIGNATURE: 1, TASK: 4}
                };

                function getBookmarks() {
                    return $http.get('/ThreatKB/bookmarks')
                        .then(function (success) {
                                if (success.status === 200 && success.data) {
                                    return success.data;
                                }
                            }, function (error) {
                                return $q.reject(error.data);
                            }
                        );
                }

                function createBookmark(entity_type, entity_id) {
                    return $http.post('/ThreatKB/bookmarks', {
                        entity_type: entity_type,
                        entity_id: entity_id
                    }).then(function (success) {
                            if (success.status === 201 && success.data) {
                                return success.data;
                            }
                        }, function (error) {
                            return $q.reject(error.data);
                        }
                    );
                }

                function deleteBookmark(entity_type, entity_id) {
                    return $http.delete('/ThreatKB/bookmarks', {
                        params: {
                            entity_type: entity_type,
                            entity_id: entity_id
                        }
                    }).then(function (success) {
                            if (success.status === 204) {
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