(function($) {

  function parseResults(results) {
    return results.split(/[\r\n]+/).map(function(row) {
      try {
        return JSON.parse(row);
      } catch (e) {
        return null;
      }
    }).filter(function(e) {
      return e != null;
    });
  }

  function mergeObjects(obj1, obj2) {
    if (typeof(obj1) === 'object' && typeof(obj2) === 'object') {
      for (var f in obj2) {
        if (obj2[f] && (!(f in obj1) || !obj1[f])) {
          obj1[f] = obj2[f];
        }
        mergeObjects(obj1[f], obj2[f]);
      }
    }
    return obj1;
  }

  function showResults(tableName, results) {
    const obj = parseResults(results).reduce(mergeObjects);
    $('#preview-label').text('"' + tableName + '"');
    $('#preview-json').jsonViewer(obj);
    $('#preview-dialog').modal();
  }

  var running = false;
  $('.run-query').click(function(e) {
    if (running) return false;
    running = true;

    const tableName = $(this).data('table');
    const query = 'SELECT * FROM ' + tableName + ' LIMIT 10';
    const icon = $(this).children('i.fa');

    icon.removeClass().addClass('fa fa-spinner fa-spin');

    $.ajax({
        method: 'POST',
        url: '/api/query',
        data: query,
        dataType: 'text'
      })
      .done(function(results) {
        showResults(tableName, results);
      }).always(function() {
        icon.removeClass().addClass('fa fa-eye');
        running = false;
      });

    return false;
  });

})(jQuery);
