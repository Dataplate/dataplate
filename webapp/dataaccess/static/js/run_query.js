(function($) {

  function columnNames(jsons) {
    var columns = [];
    jsons.forEach(function(json) {
      for (var field in json) {
        if (!columns.includes(field)) {
          columns.push(field)
        }
      }
    });
    return columns;
  }

  function toCsv(jsons) {
    var columns = columnNames(jsons);
    var csv = columns.join(',') + '\n';
    jsons.forEach(function(json) {
      for (var i = 0; i < columns.length; ++i) {
        const column = columns[i];
        var value = ''
        if (!(typeof json[column] === 'undefined')) {
          value = json[column];
          if (typeof value === 'string') {
            value = value.replace(/"/g, '""');
            if (value.search(/("|,|\n)/g) >= 0) {
              value = '"' + value + '"';
            }
          } else if (value instanceof Date) {
            value = value.toLocaleString();
          }
        }
        if (i > 0) {
          csv += ',';
        }
        csv += value;
      }
      csv += '\n';
    });
    return csv;
  }

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

  function saveResults(results, file) {
    const csv = toCsv(parseResults(results));
    const blob = new Blob([csv], {
      type: 'text/csv; encoding=UTF-8'
    });
    saveAs(blob, file);
  }

  var running = false;
  $('#run-query').click(function(e) {
    if (running) return false;
    running = true;

    var file = query_name;
    var q = query_sql;
    $('input.param').each(function() {
      const val = $(this).val().trim();
      q = q.replace('${' + $(this).attr('name') + '}', val);
      file += '_' + val.replace(/\W+/, '_');
    });
    const icon = $(this).children('i.fa');
    icon.removeClass().addClass('fa fa-spinner fa-spin');

    var url = '/api/query?';
    if ($("input[name=refresh]").is(":checked")) {
      url += 'refresh=true';
    }

    $.ajax({
        method: 'POST',
        url: url,
        data: q,
        dataType: 'text'
      })
      .done(function(results) {
        saveResults(results, file + '.csv');
      })
      .fail(function(jqXHR, textStatus, errorThrown) {
        showAlert(jqXHR.responseText);
      })
      .always(function() {
        icon.removeClass().addClass('fa fa-play');
        running = false;
      });

    return false;
  });

})(jQuery);
