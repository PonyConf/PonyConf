var csrftoken = $.cookie('csrftoken');

function csrfSafeMethod(method) {
  // these HTTP methods do not require CSRF protection
  return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
$.ajaxSetup({
  beforeSend: function(xhr, settings) {
    if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
      xhr.setRequestHeader("X-CSRFToken", csrftoken);
    }
  }
});

$('a[href="#preview"]').on("show.bs.tab", function (e) {
  $('#markdown-preview').html('Loading preview...');
  var markdown = $('#markdown-content').val();
  $.post(markdown_preview_url, {'data': markdown})
    .done(function(data, textStatus) {
      $('#markdown-preview').html(data);
    })
    .fail(function () {
      $('#markdown-preview').html('Sorry, an error occured.');
    });
})
