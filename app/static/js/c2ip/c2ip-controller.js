'use strict';

angular.module('InquestKB')
    .controller('C2ipController', ['$scope', '$modal', 'resolvedC2ip', 'C2ip', 'Cfg_states',
        function ($scope, $modal, resolvedC2ip, C2ip, Cfg_states) {

            $scope.c2ips = resolvedC2ip;

            $scope.create = function () {
                $scope.clear();
                $scope.open();
            };

            $scope.update = function (id) {
                $scope.c2ip = C2ip.get({id: id});
                $scope.cfg_states = Cfg_states.query();
                $scope.open(id);
            };

            $scope.delete = function (id) {
                C2ip.delete({id: id},
                    function () {
                        $scope.c2ips = C2ip.query();
                    });
            };

            $scope.save = function (id) {
                if (id) {
                    C2ip.update({id: id}, $scope.c2ip,
                        function () {
                            $scope.c2ips = C2ip.query();
                            //$scope.clear();
                        });
                } else {
                    C2ip.save($scope.c2ip,
                        function () {
                            $scope.c2ips = C2ip.query();
                            //$scope.clear();
                        });
                }
            };

            $scope.clear = function () {
                $scope.c2ip = {

                    "date_created": "",

                    "date_modified": "",

                    "ip": "",

                    "asn": "",

                    "country": "",

                    "city": "",

                    "state": "",

                    "reference_link": "",

                    "reference_text": "",

                    "expiration_type": "",

                    "expiration_timestamp": "",

                    "id": ""
                };
            };

            $scope.open = function (id) {
                var c2ipSave = $modal.open({
                    templateUrl: 'c2ip-save.html',
                    controller: 'C2ipSaveController',
                    resolve: {
                        c2ip: function () {
                            return $scope.c2ip;
                        }
                    }
                });

                c2ipSave.result.then(function (entity) {
                    $scope.c2ip = entity;
                    $scope.save(id);
                });
            };
        }])
    .controller('C2ipSaveController', ['$scope', '$modalInstance', 'c2ip', 'Comments', 'Cfg_states',
        function ($scope, $modalInstance, c2ip, Comments, Cfg_states) {
            $scope.c2ip = c2ip
            $scope.c2ip.new_comment = "";
            $scope.Comments = Comments;

            $scope.cfg_states = Cfg_states.query();

            $scope.add_comment = function (id) {
                $scope.Comments.resource.save({
                    comment: $scope.c2ip.new_comment,
                    entity_type: Comments.ENTITY_MAPPING.IP,
                    entity_id: id
                }, function () {
                    $scope.c2ip.new_comment = "";
                    $scope.c2ip.comments = $scope.Comments.resource.query({
                        entity_type: Comments.ENTITY_MAPPING.IP,
                        entity_id: id
                    })
                });
            };

            $scope.ok = function () {
                $modalInstance.close($scope.c2ip);
            };

            $scope.cancel = function () {
                $modalInstance.dismiss('cancel');
            };
        }]);
