'use strict';

// Wrapper directive around UI-Codemirror code editor component
// Parameters:
// - ngModel:             Bound, editing value
// - mode:                Syntax mode (example: 'yara')
// - readOnly:            Sets editor into read-only mode (Codemirror passthrough option)
// - containScrollWheel:  If true, won't allow mouse wheel scroll events to escape to parent components
// - lineNumbers:         If true, editor will display line numbers (Codemirror passthrough option)
// - lineWrapping:        If true, editor will use line wrapping (Codemirror passthrough option)
// - indentWithTabs:      If true, editor will use tabs for indentation (Codemirror passthrough option)
// - autofocus:           If true, editor will auto-focus (Codemirror passthrough option)
// - controlsWrap:        If true, will show wrap control
// - controlsFind:        If true, will show find control
// - onLoad:              On load callback
angular.module('ThreatKB').directive('tkbCodemirror', function () {
  return {
    templateUrl: 'components/tkb-codemirror/index.html',
    scope: {
      ngModel: '=',
      mode: '=',
      readOnly: '=',
      containScrollWheel: '=',
      lineNumbers: '=',
      lineWrapping: '=',
      indentWithTabs: '=',
      autofocus: '=',
      controlsWrap: '=',
      controlsFind: '=',
      onLoad: '&'
    },
    transclude: true,
    link: function ($scope, element, attrs) {

      // Process codemirror options
      $scope.$watch(
        function () {
          return {
            // Options passthrough
            mode:           (typeof $scope.mode !== 'undefined'           ? $scope.mode           : null),
            readOnly:       (typeof $scope.readOnly !== 'undefined'       ? $scope.readOnly       : false),
            lineNumbers:    (typeof $scope.lineNumbers !== 'undefined'    ? $scope.lineNumbers    : false),
            lineWrapping:   (typeof $scope.lineWrapping !== 'undefined'   ? $scope.lineWrapping   : false),
            indentWithTabs: (typeof $scope.indentWithTabs !== 'undefined' ? $scope.indentWithTabs : false),
            autofocus:      (typeof $scope.autofocus !== 'undefined'      ? $scope.autofocus      : false)
          }
        },
        function (opts) {
          // Set options
          opts.onLoad = onCoremirrorLoad;
          $scope.opts = opts;
        },
        true
      );

      // Initialize internal properties
      $scope.findExpression = null;
      $scope.searchCursor = null;

      // Initialize codemirror editor on load
      function onCoremirrorLoad (editor) {

        // Run callback
        if ($scope.onLoad) { $scope.onLoad(); }

        // Handle wheel-scroll event
        var codeMirrotVScrollEl = element[0].querySelector('.CodeMirror-vscrollbar'),
            codeMirrotVScrollFlip = 0;
        element.on('DOMMouseScroll mousewheel', function (ev) {
          if ($scope.containScrollWheel) {
            codeMirrotVScrollFlip = (codeMirrotVScrollFlip + 1) % 2;
            var scrollTop =     codeMirrotVScrollEl.scrollTop,
                scrollHeight =  codeMirrotVScrollEl.scrollHeight,
                height =        codeMirrotVScrollEl.offsetHeight,
                delta =         (ev.type == 'DOMMouseScroll' ? ev.detail * -40 : (ev.originalEvent ? ev.originalEvent.wheelDelta : ev.wheelDelta)),
                up =            delta > 0,
                prevent = () => {
                  ev.stopPropagation();
                  ev.preventDefault();
                  return false;
                };
            if (!up && -delta >= scrollHeight - height - scrollTop) {
              // Set scrolling class
              element.removeClass('scroll-top');
              element.addClass('scroll-bottom');
              if (codeMirrotVScrollFlip === 0) {
                element.removeClass('scroll-animation-a');
                element.addClass('scroll-animation-b');
              } else {
                element.removeClass('scroll-animation-b');
                element.addClass('scroll-animation-a');
              }
              // Scrolling down, but this will take us past the bottom.
              codeMirrotVScrollEl.scrollTop = scrollHeight;
              return prevent();
            } else if (up && delta > scrollTop) {
              // Set scrolling class
              element.addClass('scroll-top');
              element.removeClass('scroll-bottom');
              if (codeMirrotVScrollFlip === 0) {
                element.removeClass('scroll-animation-a');
                element.addClass('scroll-animation-b');
              } else {
                element.removeClass('scroll-animation-b');
                element.addClass('scroll-animation-a');
              }
              // Scrolling up, but this will take us past the top.
              codeMirrotVScrollEl.scrollTop = 0;
              return prevent();
            } else {
              // Set scrolling class
              element.removeClass('scroll-top');
              element.removeClass('scroll-bottom');
            }
          }
        });

        // Expose search functionality
        {
          $scope.doFind = function () {
            var findExpression = $scope.findExpression && $scope.findExpression.trim();
            if (findExpression && findExpression.length) {
              // Get new search cursor
              $scope.searchCursor = editor.getSearchCursor(findExpression, 0, { caseFold: true });
              $scope.findNext();
            } else {
              // Reset search cursor
              $scope.searchCursor = null;
              $scope.selectFound();
            }
          }
          $scope.findNext = function () {
            if ($scope.searchCursor) {
              $scope.searchCursor.findNext();
              $scope.selectFound();
            }
          }
          $scope.findPrevious = function () {
            if ($scope.searchCursor) {
              $scope.searchCursor.findPrevious();
              $scope.selectFound();
            }
          }
          $scope.cancelFind = function () {
            $scope.findExpression = null;
            $scope.doFind();
          }
          $scope.selectFound = function () {
            if ($scope.searchCursor && $scope.searchCursor.pos.from && $scope.searchCursor.pos.to) {
              $scope.searchCursor.doc.setSelection($scope.searchCursor.pos.from, $scope.searchCursor.pos.to);
            }
          }
        }

        // Intercept shortcuts
        element[0].addEventListener('keydown', function (e) {
          // Process event
          var ctrlKey = (e.ctrlKey || e.metaKey),
              shiftKey = e.shiftKey,
              enterKey = e.code === 'Enter',
              targetFindInput = (e.target.getAttribute('tkb-codemirror-find-input') !== null),
              findAction = (ctrlKey && e.code === 'KeyF'),
              findNextAction = (targetFindInput && !shiftKey && enterKey) || (ctrlKey && !shiftKey && (e.code === 'KeyG')),
              findPrevAction = (targetFindInput && shiftKey && enterKey) || (ctrlKey && shiftKey && (e.code === 'KeyG'));
          // Act on event
          if (findAction) {
            element[0].querySelector('[tkb-codemirror-find-input]').focus();
          } else if (findNextAction) {
            $scope.findNext();
          } else if (findPrevAction) {
            $scope.findPrevious();
          } else {
            return;
          }
          // Stop event propagation
          e.preventDefault();
          e.stopPropagation();
        });

      };

    }
  };
});
