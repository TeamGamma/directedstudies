$(function() {
  console.log('Initializing forms');

  // Activate tabs
  $('#command-tabs a').first().tab('show');

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
      var type = $(data.firstChild).attr('contents');
      var text = prettyPrintResponse(data.firstChild);

      showResults(type, text);
      refresh();

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

  // Hide modal window with close button
  modal.click(function() {
    modal.modal('hide');
  });

  var showResults = function(type, content) {
    // Set modal title to content type of message
    modal.find('h3').text(type[0].toUpperCase() + type.slice(1));

    // Set text content of modal
    modal.find('.modal-body').html(content);

    modal.modal('show');
  };

  var refreshbtn = $('#refresh-button');
  var refresh = function() {
    refreshbtn.addClass('disabled');

    setTimeout(function() { refreshbtn.removeClass('disabled'); }, 1000);

    // Get data from DISPLAY_SUMMARY form
    var data = $('.command-form[action="/DISPLAY_SUMMARY"]').serialize();
    $.post('/DISPLAY_SUMMARY', data, function(data) {
      var response = data.firstChild;
      window.response = response;
      console.log(response);

      // Set account balance and reserve balance
      $('#account-balance').text($(response).find('account_balance').text());
      $('#reserve-balance').text($(response).find('reserve_balance').text());

      // Empty out transactions, stocks, and triggers
      $('#transaction-table tbody tr').remove();
      $('#stock-table tbody tr').remove();
      $('#trigger-table tbody >tr').remove();

      // Add transactions
      $(response).find('transaction').each(function() {
        var attr = attributeMap(this);
        attr.status_icon = {True: 'icon-ok', False: 'icon-time'}[attr.committed];
        var tr = ich.transaction(attr);
        $('#transaction-table tbody').append(tr);
      });

      // Add stocks
      $(response).find('stock').each(function() {
        var attr = attributeMap(this);
        var tr = ich.stock(attr);
        $('#stock-table tbody').append(tr);
      });

      // Add triggers
      $(response).find('trigger').each(function() {
        var attr = attributeMap(this);
        attr.amount = ('amount' in attr)? attr.amount : '...';
        attr.quantity = ('quantity' in attr)? attr.quantity : '...';
        attr.status_icon = {INACTIVE: 'icon-ok', RUNNING: 'icon-repeat', CANCELLED: 'icon-remove'}[attr.state];
        var tr = ich.trigger(attr);
        $('#trigger-table tbody').append(tr);
      });

      refreshbtn.removeClass('disabled');
    }, 'xml');

    return false;
  };
  refreshbtn.click(refresh);
  refresh();

});

var attributeMap = function(element) {
  var attributes = element.attributes;
  var attrMap = {};
  for(var i=0; i<attributes.length; i++) {
    var attr = attributes[i];
    attrMap[attr.name] = attr.value;
  }
  return attrMap;
};

var prettyPrintResponse = function(response) {
  var output = "";
  Array.prototype.forEach.call(response.childNodes, function(element) {
    output += _prettyPrintTree(element, "");
  });
  return output;
};
var _prettyPrintTree = function(dom, indent) {
  var output = indent;
  if(dom.nodeType === document.TEXT_NODE) {
    // Text node
    output += dom.nodeValue + '\n';
    return output;
  } else if(dom.childNodes.length === 1 &&
            dom.firstChild.nodeType == document.TEXT_NODE &&
            dom.attributes.length === 0) {
    // Element node containing single text node
    output += '<strong>' + dom.nodeName + '</strong>';
    output += ' = ' + dom.firstChild.nodeValue + '\n';
    return output;
  }

  // Element node
  output += '<strong>' + dom.nodeName + '</strong>\n';
  $.each(attributeMap(dom), function(key, value) {
    output += indent + "    <em>" + key + '</em>: ' + value + '\n';
  });

  Array.prototype.forEach.call(dom.childNodes, function(child) {
    output += _prettyPrintTree(child, indent + "    ");
  });
 
  return output;
};

