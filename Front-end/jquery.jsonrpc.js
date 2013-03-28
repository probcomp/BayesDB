/*
 * jQuery JSON-RPC Plugin
 *
 * @version: 0.2-alpha(2010-08-24)
 * @author hagino3000 <http://twitter.com/hagino3000> (Takashi Nishibayashi)
 * @author alanjds <http://twitter.com/alanjds> (Alan Justino da Silva)
 * @author MiCHiLU <http://twitter.com/MiCHiLU> (Takanao ENDOH)
 *
 * A JSON-RPC 2.0 implementation for jQuery.
 * JSON-RPC is a stateless, light-weight remote procedure call (RPC) protocol.
 * Read more in the <http://groups.google.com/group/json-rpc/web/json-rpc-2-0>
 *
 * Requires json2.js<http://www.json.org/json2.js> if browser has not window.JSON.
 *
 * Usage:
 *   $.jsonrpc(url, data [, callbacks] [, debug]);
 *
 *   where data = {method:'methodname', params:['positional', 'parameters']}
 *   or data = {method:'complexmethod', params:{named:'parameters', works:'too!'}}
 *   and callbacks = {success: successFunc, fault: faultFunc, error: errorFunc}
 *
 *   Setting no callback produces a JSON-RPC Notification.
 *   'data' accepts 'timeout' keyword too, who sets the $.ajax request timeout.
 *   Setting 'debug' to true prints responses to Firebug's console.info
 *
 *   $.jsonrpcBind(url, method [, callbacks] [, timeout] [, debug]);
 *
 * Examples:
 *   // A RPC call with named parameters
 *   $.jsonrpc('/rpc', {
 *     method : 'createUser',
 *     params : {name : 'John Smith', userId : '1000'}
 *   }, {
 *     success : doSomething(response),
 *     fault : handleFault(response, errordata),
 *     error : handleError(request, status, error);
 *   });
 *
 *   // A Notification 
 *   $.jsonrpc('/rpc', {
 *     method : 'notify',
 *     params : {action : 'logout', userId : '1000'}
 *   });
 *
 *   // A Notification using console to debug and with timeout set
 *   $.jsonrpc('/rpc', {
 *     method : 'notify',
 *     params : {action : 'logout', userId : '1000'},
 *     debug : true,
 *     timeout : 500,
 *   });
 *
 *   // Bind to RPC call
 *   var $createUser = $.jsonrpc('/rpc', 'createUser', {
 *     success : doSomething(response),
 *     fault : handleFault(response, errordata),
 *     error : handleError(request, status, error);
 *   });
 *   var $notify = $.jsonrpcBind('/rpc', 'notify', 500, true);
 *   $createUser({name : 'John Smith', userId : '1000'});
 *   $notify({action : 'login', userId : '1000'});
 *   $notify({action : 'logout', userId : '1000'});
 *
 * This document is licensed as free software under the terms of the
 * MIT License: http://www.opensource.org/licenses/mit-license.php
 */
(function($) {
   
  var rpcid = 1;
   
  $.jsonrpc = $.jsonrpc || function(url, data, callbacks, debug) {
   
    var postdata = {
      jsonrpc : '2.0',
      method : data.method || '',
      params : data.params || {}
    }
    if (callbacks) {
      postdata.id = data.id || rpcid++;
    }
   
    debug = debug || false

    var ajaxopts = {
      url : url,
      contentType : 'application/json',
      dataType : 'json',
      type : 'POST',
      dataFilter: function(data, type) {
        if (debug && console != undefined) console.info(data);
        return JSON.parse(data);
      },
      processData : false,
      data : JSON.stringify(postdata),
      success : function(resp) {
        if (resp && !resp.error) return callbacks.success && callbacks.success(resp.result);
        else if (resp && resp.error) return callbacks.fault && callbacks.fault(resp.error.message, resp.error.data);
        else return callbacks.fault && callbacks.fault(resp);
      },
      error : function(xhr, status, error) {
        return callbacks.error && callbacks.error(xhr, status, error);
      }
    }
    if (data.timeout){
      ajaxopts['timeout'] = data.timeout
    }
    
    $.ajax(ajaxopts);

    return $;
  }

  $.jsonrpcBind = $.jsonrpcBind || function(url, method, callbacks, timeout, debug) {

    var jsonrpc = function(params) {
      var postdata = {
        jsonrpc : '2.0',
        method : method || '',
        params : params || {}
      }
      if (callbacks) {
        postdata.id = rpcid++;
      }

      debug = debug || false

      var ajaxopts = {
        url : url,
        contentType : 'application/json',
        dataType : 'json',
        type : 'POST',
        dataFilter: function(data, type) {
          if (debug && console != undefined) console.info(data);
          return JSON.parse(data);
        },
        processData : false,
        data : JSON.stringify(postdata),
        success : function(resp) {
          if (resp && !resp.error) return callbacks.success && callbacks.success(resp.result);
          else if (resp && resp.error) return callbacks.fault && callbacks.fault(resp.error.message, resp.error.data);
          else return callbacks.fault && callbacks.fault(resp);
        },
        error : function(xhr, status, error) {
          return callbacks.error && callbacks.error(xhr, status, error);
        }
      }
      if (timeout){
        ajaxopts['timeout'] = timeout
      }

      $.ajax(ajaxopts);
    }

    return jsonrpc;
  }

})(jQuery);

