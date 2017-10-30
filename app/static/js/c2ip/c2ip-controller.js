'use strict';

angular.module('ThreatKB')
    .controller('C2ipController', ['$scope', '$filter', '$http', '$uibModal', 'resolvedC2ip', 'C2ip', 'Cfg_states', 'growl', 'Users',
        function ($scope, $filter, $http, $uibModal, resolvedC2ip, C2ip, Cfg_states, growl, Users) {

            $scope.c2ips = resolvedC2ip;

            $scope.users = Users.query();

            $scope.filterOptions = {
                filterText: ''
            };

            var paginationOptions = {
                pageNumber: 1,
                pageSize: 25
            };

            $scope.gridOptions = {
                paginationPageSizes: [25, 50, 75, 100],
                paginationPageSize: 25,
                useExternalPagination: true,
                enableFiltering: true,
                flatEntityAccess: true,
                fastWatch: true,
                onRegisterApi: function (gridApi) {
                    $scope.gridApi = gridApi;
                    gridApi.pagination.on.paginationChanged($scope, function (newPage, pageSize) {
                        paginationOptions.pageNumber = newPage;
                        paginationOptions.pageSize = pageSize;
                        getPage();
                    });
                },
                rowHeight: 35,
                columnDefs:
                    [
                        {field: 'ip', displayName: 'IP'},
                        {field: 'state'},
                        {field: 'asn', displayName: 'ASN'},
                        {field: 'country'},
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
                            + '&nbsp;'
                            + '<button ng-click="grid.appScope.delete(row.entity.id)"'
                            + ' ng-confirm-click="Are you sure you want to '
                            + 'delete this c2ip?" class="btn btn-sm btn-danger">'
                            + '<small>'
                            + '<span class="glyphicon glyphicon-remove-circle"></span>'
                            + '</small>'
                            + '</button></div>'
                        }
                    ]
            };

            var getPage = function () {
                $http.get('/ThreatKB/c2ips')
                    .then(function (response) {
                        $scope.gridOptions.totalItems = response.data.length;
                        var firstRow = (paginationOptions.pageNumber - 1) * paginationOptions.pageSize;
                        $scope.gridOptions.data = response.data.slice(firstRow, firstRow + paginationOptions.pageSize);
                    }, function (error) {
                    });
            };

            $scope.refreshData = function () {
                $scope.gridOptions.data = $filter('filter')($scope.c2ips, $scope.searchText, undefined);
            };

            $scope.create = function () {
                $scope.clear();
                $scope.open();
            };

            $scope.update = function (id) {
                $scope.c2ip = C2ip.get({id: id});
                $scope.cfg_states = Cfg_states.query();
                $scope.users = Users.query();
                $scope.open(id);
            };

            $scope.delete = function (id) {
                C2ip.delete({id: id}, function () {
                    $scope.c2ips = C2ip.query();
                    $scope.gridOptions.data = $scope.c2ips;
                    $scope.refreshData();
                });
            };

            $scope.save = function (id_or_ip) {
                var id = id_or_ip;
                if (typeof(id_or_ip) === "object") {
                    id = id_or_ip.id;
                    $scope.c2ip = id_or_ip;
                }

                if (id) {
                    C2ip.update({id: id}, $scope.c2ip, function () {
                        $scope.c2ips = C2ip.query();
                        $scope.gridOptions.data = $scope.c2ips;
                        $scope.refreshData();
                    }, function (error) {
                        growl.error(error.data, {ttl: -1});
                    });
                } else {
                    C2ip.save($scope.c2ip, function () {
                        $scope.c2ips = C2ip.query();
                        $scope.gridOptions.data = $scope.c2ips;
                        $scope.refreshData();
                    }, function (error) {
                        growl.error(error.data, {ttl: -1});
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
                var c2ipSave = $uibModal.open({
                    templateUrl: 'c2ip-save.html',
                    controller: 'C2ipSaveController',
                    size: 'lg',
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

            getPage();
        }])
    .controller('C2ipSaveController', ['$scope', '$http', '$uibModalInstance', 'c2ip', 'Comments', 'Cfg_states', 'Tags',
        function ($scope, $http, $uibModalInstance, c2ip, Comments, Cfg_states, Tags) {
            $scope.c2ip = c2ip;
            $scope.c2ip.new_comment = "";
            $scope.Comments = Comments;

            $scope.cfg_states = Cfg_states.query();

            $scope.print_comment = function (comment) {
                return comment.comment.replace(/(?:\r\n|\r|\n)/g, "<BR>");
            };

            $scope.add_comment = function (id) {
                if (!$scope.c2ip.new_comment) {
                    return;
                }

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
                $uibModalInstance.close($scope.c2ip);
            };

            $scope.cancel = function () {
                $uibModalInstance.dismiss('cancel');
            };

            $scope.addedTag = function ($tag) {
                $scope.c2ip.addedTags.push($tag)
            };

            $scope.removedTag = function ($tag) {
                $scope.c2ip.removedTags.push($tag)
            };

            $scope.loadTags = function (query) {
                return Tags.loadTags(query);
            };
        }]);
