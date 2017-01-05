(function() {
  // Union of Chrome, Firefox, IE, Opera, and Safari console methods
  var methods = ["assert", "cd", "clear", "count", "countReset",
    "debug", "dir", "dirxml", "error", "exception", "group", "groupCollapsed",
    "groupEnd", "info", "log", "markTimeline", "profile", "profileEnd",
    "select", "table", "time", "timeEnd", "timeStamp", "timeline",
    "timelineEnd", "trace", "warn"];
  var length = methods.length;
  var console = (window.console = window.console || {});
  var method;
  var noop = function() {};
  while (length--) {
    method = methods[length];
    // define undefined methods as noops to prevent errors
    if (!console[method])
      console[method] = noop;
  }
})();

var mylar = {
	
	debug: true,

	config: {
		console: {
			sendToServer: false
		},
		notify: {
			default: {
				options: {
					icon: 'glyphicon glyphicon-info-sign'
				},
				settings: {
					placement: {
						from: "bottom",
						align: "right"
					},
					offset: {
						y: 70,
						x: 20
					}
				}
			},
			info : {
				options: {
					icon: 'glyphicon glyphicon-info-sign'
				},
				settings: {
					type: 'info'
				}
			},
			success : {
				options: {
					icon: 'glyphicon glyphicon-ok-circle'
				},
				settings: {
					type: 'success'
				}
			},
			warn : {
				options: {
					icon: 'glyphicon glyphicon-exclamation-sign'
				},
				settings: {
					type: 'warning'
				}
			},
			error : {
				options: {
					icon: 'glyphicon glyphicon-fire'
				},
				settings: {
					type: 'danger',
					allow_dismiss: false
				}
			},
		}
	},

	pubsub: {},
	screens: [],
	urlData: [],
	configData: [],

	init: function(){
		$(document).ready( mylar.docReady );
		$(window).on( 'load', mylar.windowLoad );
		$(window).on( 'resize', mylar.windowResize );
		$(window).on( 'unload', mylar.windowUnload );
	},
	docReady: function(){
		mylar.console.log('Into main app docReady');
		$('[data-toggle="popover"]').popover()
		
	},
	windowLoad: function(){},
	windowResize: function(){},
	windowUnload: function(){},

	registerScreen: function(){
		var screenObj = arguments[0];

		if( arguments.length > 1 ) var matchingURLs = arguments[1];
		else matchingURLs = [];
		
		if( arguments.length > 2 ) var screenConfig = arguments[2];
		else screenConfig = {};

		this.screens.push( screenObj );
		this.urlData.push( matchingURLs );
		this.configData.push( screenConfig );

		if( screenObj.hasOwnProperty('init') ){
			screenObj.init();
		}
		if( screenObj.hasOwnProperty('docReady') ){
			$(document).ready( screenObj.docReady );
		}
		if( screenObj.hasOwnProperty('windowLoad') ){
			$(window).on( 'load', screenObj.windowLoad );
		}
		if( screenObj.hasOwnProperty('windowResize') ){
			$(window).on('resize', screenObj.windowResize );
		}
		if( screenObj.hasOwnProperty('destroyScreen') ){
			$(window).on('unload', screenObj.destroyScreen );
		}

	},

	initTable: function( target ){
		target.tablesorter({
			theme : "bootstrap",
			widthFixed: true,
			headerTemplate : '{content} {icon}',

			widgets : [ "uitheme", "filter", "zebra" ],

			widgetOptions : {
				zebra : ["even", "odd"],
				filter_reset : ".reset",
				filter_cssFilter: "form-control",
			}
		})
		.tablesorterPager({
			container: $(".ts-pager"),
			cssGoto  : ".pagenum",
			removeRows: false,
			output: '{startRow} - {endRow} / {filteredRows} ({totalRows})'

		});
	},
	notify: {
		info: function(message){

			var messageOptions  = ( arguments.length > 1 ) ? $.extend(mylar.config.notify.info.options, arguments[1]) : mylar.config.notify.info.options;
			var messageSettings = ( arguments.length > 2 ) ? $.extend(mylar.config.notify.info.settings, arguments[2]) : mylar.config.notify.info.settings;

			messageOptions.message = message;

			mylar.notify.show( messageOptions, messageSettings );
		},
		success: function(message){

			var messageOptions  = ( arguments.length > 1 ) ? $.extend(mylar.config.notify.success.options, arguments[1]) : mylar.config.notify.success.options;
			var messageSettings = ( arguments.length > 2 ) ? $.extend(mylar.config.notify.success.settings, arguments[2]) : mylar.config.notify.success.settings;

			messageOptions.message = message;

			mylar.notify.show( messageOptions, messageSettings );
		},
		warn: function(message){

			var messageOptions  = ( arguments.length > 1 ) ? $.extend(mylar.config.notify.warn.options, arguments[1]) : mylar.config.notify.warn.options;
			var messageSettings = ( arguments.length > 2 ) ? $.extend(mylar.config.notify.warn.settings, arguments[2]) : mylar.config.notify.warn.settings;

			messageOptions.message = message;

			mylar.notify.show( messageOptions, messageSettings );
		},
		error: function(message){

			var messageOptions  = ( arguments.length > 1 ) ? $.extend(mylar.config.notify.error.options, arguments[1]) : mylar.config.notify.error.options;
			var messageSettings = ( arguments.length > 2 ) ? $.extend(mylar.config.notify.error.settings, arguments[2]) : mylar.config.notify.error.settings;

			messageOptions.message = message;

			mylar.notify.show( messageOptions, messageSettings );
		},
		show: function(options,settings){
			var messageOptions  = $.extend(mylar.config.notify.default.options, options);
			var messageSettings = $.extend(mylar.config.notify.default.settings, settings);
			if( mylar.debug ) mylar.console.log(options,settings);
			$.notify( messageOptions, messageSettings );
		}
	},
	console: {
		_sendToServer: function(data){
			if( mylar.config.console.sendToServer ){
				// TODO: Send Errors to Server for Persistent Logging	
			}
		},
		error: function(){
			console.error( arguments );
			mylar.console._sendToServer( arguments );
		},
		info: function(){
			console.info( arguments );
			mylar.console._sendToServer( arguments );	
		},
		log: function(){
			console.log( arguments );
			mylar.console._sendToServer( arguments );
		},
		table: function(){
			console.table( arguments );
			mylar.console._sendToServer( arguments );
		},
		warn: function(){
			console.warn( arguments );
			mylar.console._sendToServer( arguments );
		}

	}
}

mylar.init();

/* https://gist.github.com/fatihacet/1290216 */
mylar.pubsub = {};
(function(q) {
    var topics = {}, subUid = -1;
    q.subscribe = function(topic, func) {
        if (!topics[topic]) {
            topics[topic] = [];
        }
        var token = (++subUid).toString();
        topics[topic].push({
            token: token,
            func: func
        });
        return token;
    };

    q.publish = function(topic, args) {
        if (!topics[topic]) {
            return false;
        }
        setTimeout(function() {
            var subscribers = topics[topic],
                len = subscribers ? subscribers.length : 0;

            while (len--) {
                subscribers[len].func(topic, args);
            }
        }, 0);
        return true;

    };

    q.unsubscribe = function(token) {
        for (var m in topics) {
            if (topics[m]) {
                for (var i = 0, j = topics[m].length; i < j; i++) {
                    if (topics[m][i].token === token) {
                        topics[m].splice(i, 1);
                        return token;
                    }
                }
            }
        }
        return false;
    };
}(mylar.pubsub));