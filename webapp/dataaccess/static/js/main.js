(function($) {

  $(".sidebar-dropdown > a").click(function() {
    $(".sidebar-submenu").slideUp(200);
    if ($(this).parent().hasClass("active")) {
      $(".sidebar-dropdown").removeClass("active");
      $(this).parent().removeClass("active");
    } else {
      $(".sidebar-dropdown").removeClass("active");
      $(this).next(".sidebar-submenu").slideDown(200);
      $(this).parent().addClass("active");
    }
  });

  $("#close-sidebar").click(function() {
    $(".page-wrapper").removeClass("toggled");
  });

  $("#show-sidebar").click(function() {
    $(".page-wrapper").addClass("toggled");
  });

  $('.typeahead').each(function() {
    const inputElement = $(this);
    $.getJSON(inputElement.data('source-url'), function(data) {
      inputElement.typeahead({
        source: data,
        matcher: function(item) {
          const existing = this.$element.val().split(/[\s,]+/);
          existing.pop();
          const it = this.displayText(item);
          const prefix = this.query.replace(/.*\S[\s,]+/s, '').toLowerCase();
          return !existing.find(function(e) {
            return e == item;
          }) && prefix.length > 0 && ~it.toLowerCase().indexOf(prefix)
        },
        updater: function(item) {
          return this.$element.val().replace(/\S+$/s, '') + item;
        },
        highlighter: function(item) {
          var query = this.query.replace(/.*\s+/s, '').replace(/[\-\[\]{}()*+?.,\\\^$|#\s]/g, '\\$&')
          return item.replace(new RegExp('(' + query + ')', 'ig'), function($1, match) {
            return '<strong>' + match + '</strong>'
          })
        }
      });
    });
  });

  window.showAlert = function(message) {
    $('.alert-container').html(
      $('<div/>').addClass('alert alert-danger alert-dismissable').append(
        $('<button/>').addClass('close').attr('type', 'button')
        .attr('data-dismiss', 'alert').attr('aria-hidden', 'true').html('&times;')
      ).append(message));
  };

  $('[data-toggle="tooltip"]').tooltip();

})(jQuery);
