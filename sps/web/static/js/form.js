var result = null;

$(function() {
  console.log('Initializing forms');

  var modal = $('#command-output-modal');

  // Submit command form
  $('.command-form').submit(function() {
    var form = $(this);

    // Check for missing form fields
    form.find('.control-group').removeClass('error');
    var fail = false;
    form.find('input').each(function() {
      var input = $(this);
      console.log(input.attr('value')); 
      if(input.attr('value').length === 0) {
        input.parent().parent().addClass('error');
        fail = true;
      }
    });
    if(fail) { return false; }

    var url = $(this).attr('action');
    var data = $(this).serialize();

    $.post(url, data, function(data) {
      console.log(data);
      result = data;
      var type = $(data.firstChild).attr('contents');
      var message = data.firstChild.firstChild;

      // Set modal content to XML for now
      var text = new XMLSerializer().serializeToString(message);

      showResults(type, text);

    }, 'xml').error(function(xhr, status, textResponse) {
      var data, type, text;

      // Try to parse as XML, fall back on textResponse
      try {
        data = $.parseXML(xhr.responseText);
        type = $(data.firstChild).attr('contents');
        text = data.firstChild.firstChild.textContent;
      } catch(err) {
        type = 'error';
        text = textResponse;
      }

      // Show contents of error tag
      showResults(type, text);
    });

    return false;
  });

  // Activate tabs
  $('#command-tabs a').first().tab('show');

  // Hide modal window with close button
  modal.click(function() {
    modal.modal('hide');
  });

  var showResults = function(type, text) {
    // Set modal title to content type of message
    modal.find('h3').text(type[0].toUpperCase() + type.slice(1));

    // Set text content of modal
    modal.find('.modal-body p').text(text);

    modal.modal('show');
  };
});

function htmlEscape(str) {
    return String(str)
            .replace(/&/g, '&amp;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
}
