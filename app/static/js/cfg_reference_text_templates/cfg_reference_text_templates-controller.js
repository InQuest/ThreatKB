'use strict';

angular.module('InquestKB')
    .controller('Cfg_reference_text_templatesController', ['$scope', '$uibModal', 'resolvedCfg_reference_text_templates', 'Cfg_reference_text_templates',
        function ($scope, $uibModal, resolvedCfg_reference_text_templates, Cfg_reference_text_templates) {

            $scope.cfg_reference_text_templates = resolvedCfg_reference_text_templates;

            $scope.create = function () {
                $scope.clear();
                $scope.open();
            };

            $scope.update = function (id) {
                $scope.cfg_reference_text_templates = Cfg_reference_text_templates.get({id: id});
                $scope.open(id);
            };

            $scope.delete = function (id) {
                Cfg_reference_text_templates.delete({id: id},
                    function () {
                        $scope.cfg_reference_text_templates = Cfg_reference_text_templates.query();
                    });
            };

            $scope.save = function (id) {
                if (id) {
                    Cfg_reference_text_templates.update({id: id}, $scope.cfg_reference_text_templates,
                        function () {
                            $scope.cfg_reference_text_templates = Cfg_reference_text_templates.query();
                            //$scope.clear();
                        });
                } else {
                    Cfg_reference_text_templates.save($scope.cfg_reference_text_templates,
                        function () {
                            $scope.cfg_reference_text_templates = Cfg_reference_text_templates.query();
                            //$scope.clear();
                        });
                }
            };

            $scope.clear = function () {
                $scope.cfg_reference_text_templates = {

                    "template_text": "",

                    "id": ""
                };
            };

            $scope.open = function (id) {
                var cfg_reference_text_templatesSave = $uibModal.open({
                    templateUrl: 'cfg_reference_text_templates-save.html',
                    controller: 'Cfg_reference_text_templatesSaveController',
                    resolve: {
                        cfg_reference_text_templates: function () {
                            return $scope.cfg_reference_text_templates;
                        }
                    }
                });

                cfg_reference_text_templatesSave.result.then(function (entity) {
                    $scope.cfg_reference_text_templates = entity;
                    $scope.save(id);
                }, function (error) {
                    growl.error(error, {ttl: -1});
                });
            };
        }])
    .controller('Cfg_reference_text_templatesSaveController', ['$scope', '$uibModalInstance', 'cfg_reference_text_templates',
        function ($scope, $uibModalInstance, cfg_reference_text_templates) {
            $scope.cfg_reference_text_templates = cfg_reference_text_templates;


            $scope.ok = function () {
                $uibModalInstance.close($scope.cfg_reference_text_templates);
            };

            $scope.cancel = function () {
                $uibModalInstance.dismiss('cancel');
            };
        }]);
