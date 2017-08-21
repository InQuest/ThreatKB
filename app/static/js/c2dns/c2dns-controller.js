'use strict';

angular.module('InquestKB')
    .controller('C2dnsController', ['$scope', '$uibModal', 'resolvedC2dns', 'C2dns', 'Cfg_states',
        function ($scope, $uibModal, resolvedC2dns, C2dns, Cfg_states) {

            $scope.c2dns = resolvedC2dns;

            $scope.create = function () {
                $scope.clear();
                $scope.open();
            };

            $scope.update = function (id) {
                $scope.c2dns = C2dns.get({id: id});
                $scope.cfg_states = Cfg_states.query();
                $scope.open(id);
            };

            $scope.delete = function (id) {
                C2dns.delete({id: id}, function () {
                    $scope.c2dns = C2dns.query();
                });
            };

            $scope.save = function (id) {
                if (id) {
                    C2dns.update({id: id}, $scope.c2dns, function () {
                        $scope.c2dns = C2dns.query();
                        //$scope.clear();
                    });
                } else {
                    C2dns.save($scope.c2dns, function () {
                        $scope.c2dns = C2dns.query();
                        //$scope.clear();
                    });
                }
            };

            $scope.clear = function () {
                $scope.c2dns = {

                    "date_created": "",

                    "date_modified": "",

                    "state": "",

                    "domain_name": "",

                    "match_type": "",

                    "reference_link": "",

                    "reference_text": "",

                    "expiration_type": "",

                    "expiration_timestamp": "",

                    "id": "",

                    "tags": [],

                    "addedTags": [],

                    "removedTags": []
                };
            };

            $scope.open = function (id) {
                var c2dnsSave = $uibModal.open({
                    templateUrl: 'c2dns-save.html',
                    controller: 'C2dnsSaveController',
                    size: 'lg',
                    resolve: {
                        c2dns: function () {
                            return $scope.c2dns;
                        }
                    }
                });

                c2dnsSave.result.then(function (entity) {
                    $scope.c2dns = entity;
                    $scope.save(id);
                }, function (error) {
                    growl.error(error, {ttl: -1});
                });
            };
        }])
    .controller('C2dnsSaveController', ['$scope', '$http', '$uibModalInstance', 'c2dns', 'Cfg_states', 'Comments',
        function ($scope, $http, $uibModalInstance, c2dns, Cfg_states, Comments) {
            $scope.c2dns = c2dns;
            $scope.c2dns.new_comment = "";
            $scope.Comments = Comments;

            $scope.cfg_states = Cfg_states.query();

            $scope.print_comment = function (comment) {
                return comment.comment.replace(/(?:\r\n|\r|\n)/g, "<BR>");
            };

            $scope.add_comment = function (id) {
                if (!$scope.c2dns.new_comment) {
                    return;
                }

                $scope.Comments.resource.save({
                    comment: $scope.c2dns.new_comment,
                    entity_type: Comments.ENTITY_MAPPING.DNS,
                    entity_id: id
                }, function () {
                    $scope.c2dns.new_comment = "";
                    $scope.c2dns.comments = $scope.Comments.resource.query({
                        entity_type: Comments.ENTITY_MAPPING.DNS,
                        entity_id: id
                    })
                });
            };

            $scope.ok = function () {
                $uibModalInstance.close($scope.c2dns);
            };

            $scope.cancel = function () {
                $uibModalInstance.dismiss('cancel');
            };

            $scope.addedTag = function ($tag) {
                $scope.c2dns.addedTags.push($tag)
            };

            $scope.removedTag = function ($tag) {
                $scope.c2dns.removedTags.push($tag)
            };

            $scope.loadTags = function (query) {
                return $http.get('/InquestKB/tags', {cache: false}).then(function (response) {
                    var tags = response.data;
                    return tags.filter(function (tag) {
                        return tag.text.toLowerCase().indexOf(query.toLowerCase()) !== -1;
                    });
                }, function (error) {
                    growl.error(error, {ttl: -1});
                });
            }
        }]);
