'use strict';

angular.module('ThreatKB')
    .controller('C2dnsController', ['$scope', '$filter', '$http', '$uibModal', 'resolvedC2dns', 'C2dns', 'Cfg_states', 'growl', 'Users',
        function ($scope, $filter, $http, $uibModal, resolvedC2dns, C2dns, Cfg_states, growl, Users) {

            $scope.c2dns = resolvedC2dns;

            $scope.users = Users.query();

            $scope.filterOptions = {
                filterText: ''
            };

            $scope.gridOptions = {
                enableFiltering: true,
                onRegisterApi: function (gridApi) {
                    $scope.gridApi = gridApi;
                },
                columnDefs:
                    [
                        {field: 'domain_name'},
                        {field: 'state'},
                        {field: 'match_type'},
                        {field: 'expiration_type'},
                        {
                            field: 'owner_user.email',
                            displayName: 'Owner',
                            width: '20%',
                            cellTemplate: '<ui-select append-to-body="true" ng-model="row.entity.owner_user"'
                            + ' on-select="grid.appScope.save(row.entity)">'
                            + '<ui-select-match placeholder="Select an owner ...">'
                            + '<small><span ng-bind="$select.selected.email || row.entity.owner_user.email"></span></small>'
                            + '</ui-select-match>'
                            + '<ui-select-choices'
                            + ' repeat="person in (grid.appScope.users | filter: $select.search) track by person.id">'
                            + '<small><span ng-bind="person.email"></span></small>'
                            + '</ui-select-choices>'
                            + '</ui-select>'
                            + '</div>'
                        },
                        {
                            name: 'Actions',
                            enableFiltering: false,
                            enableColumnMenu: false,
                            enableSorting: false,
                            cellTemplate: '<div style="text-align: center;">'
                            + '<button type="button" ng-click="grid.appScope.update(row.entity.id)"'
                            + ' class="btn btn-sm">'
                            + '<small><span class="glyphicon glyphicon-pencil"></span>'
                            + '</small>'
                            + '</button>'
                            + '<button ng-click="grid.appScope.delete(row.entity.id)"'
                            + ' ng-confirm-click="Are you sure you want to '
                            + 'delete this c2dns?" class="btn btn-sm btn-danger">'
                            + '<small>'
                            + '<span class="glyphicon glyphicon-remove-circle"></span>'
                            + '</small>'
                            + '</button></div>'
                        }
                    ]
            };

            $scope.refreshData = function () {
                $scope.gridOptions.data = $filter('filter')($scope.c2dns, $scope.searchText, undefined);
            };

            $http.get('/ThreatKB/c2dns')
                .then(function (response) {
                    $scope.gridOptions.data = response.data;
                }, function (error) {
                });

            $scope.create = function () {
                $scope.clear();
                $scope.open();
            };

            $scope.update = function (id) {
                $scope.c2dns = C2dns.get({id: id});
                $scope.cfg_states = Cfg_states.query();
                $scope.users = Users.query();
                $scope.open(id);
            };

            $scope.delete = function (id) {
                C2dns.delete({id: id}, function () {
                    $scope.c2dns = C2dns.query();
                    $scope.gridOptions.data = $scope.c2dns;
                });
            };

            $scope.save = function (id_or_dns) {
                var id = id_or_dns;
                if (typeof(id_or_dns) === "object") {
                    id = id_or_dns.id;
                    $scope.c2dns = id_or_dns;
                }

                if (id) {
                    C2dns.update({id: id}, $scope.c2dns, function () {
                        $scope.c2dns = C2dns.query();
                        $scope.gridOptions.data = $scope.c2dns;
                    }, function (error) {
                        growl.error(error.data, {ttl: -1});
                    });
                } else {
                    C2dns.save($scope.c2dns, function () {
                        $scope.c2dns = C2dns.query();
                        $scope.gridOptions.data = $scope.c2dns;
                    }, function (error) {
                        growl.error(error.data, {ttl: -1});
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
                });
            };
        }])
    .controller('C2dnsSaveController', ['$scope', '$http', '$uibModalInstance', 'c2dns', 'Cfg_states', 'Comments',
        function ($scope, $http, $uibModalInstance, c2dns, Cfg_states, Comments) {
            $scope.c2dns = c2dns;
            $scope.c2dns.new_comment = "";
            $scope.Comments = Comments;


            $scope.match_types = ['exact', 'wildcard'];
            if (!$scope.c2dns.match_type) {
                $scope.c2dns.match_type = $scope.match_types[0];
            }

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
                return $http.get('/ThreatKB/tags', {cache: false}).then(function (response) {
                    var tags = response.data;
                    return tags.filter(function (tag) {
                        return tag.text.toLowerCase().indexOf(query.toLowerCase()) !== -1;
                    });
                }, function (error) {
                    growl.error(error.data, {ttl: -1});
                });
            }
        }]);
