'use strict';

angular.module('InquestKB')
    .controller('C2ipController', ['$scope', '$modal', 'resolvedC2ip', 'C2ip',
        function ($scope, $modal, resolvedC2ip, C2ip) {

            $scope.c2ips = resolvedC2ip;

            $scope.create = function () {
                $scope.clear();
                $scope.open();
            };

            $scope.update = function (id) {
                $scope.c2ip = C2ip.get({id: id});
                $scope.open(id);
            };

            $scope.delete = function (id) {
                C2ip.delete({id: id}, function () {
                    $scope.c2ips = C2ip.query();
                });
            };

            $scope.save = function (id) {
                if (id) {
                    C2ip.update({id: id}, $scope.c2ip, function () {
                        $scope.c2ips = C2ip.query();
                        //$scope.clear();
                    });
                } else {
                    C2ip.save($scope.c2ip, function () {
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

                    "id": "",

                    "tags": [],

                    "addedTags": [],

                    "removedTags": []
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
    .controller('C2ipSaveController', ['$scope', '$http', '$modalInstance', 'c2ip',
        function ($scope, $http, $modalInstance, c2ip) {
            $scope.c2ip = c2ip;


            $scope.date_createdDateOptions = {
                dateFormat: 'yy-mm-dd'
            };
            $scope.date_modifiedDateOptions = {
                dateFormat: 'yy-mm-dd'
            };
            $scope.expiration_timestampDateOptions = {
                dateFormat: 'yy-mm-dd',
                minDate: 1
            };

            $scope.ok = function () {
                $modalInstance.close($scope.c2ip);
            };

            $scope.cancel = function () {
                $modalInstance.dismiss('cancel');
            };

            $scope.addedTag = function ($tag) {
                $scope.c2ip.addedTags.push($tag)
            };

            $scope.removedTag = function ($tag) {
                $scope.c2ip.removedTags.push($tag)
            };

            $scope.loadTags = function (query) {
                return $http.get('/InquestKB/tags', {cache: false}).then(function (response) {
                    var tags = response.data;
                    return tags.filter(function (tag) {
                        return tag.text.toLowerCase().indexOf(query.toLowerCase()) !== -1;
                    });
                });
            }
        }]);
