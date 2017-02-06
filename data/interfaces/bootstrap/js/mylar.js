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

var mylar = $.extend({},mylar,{
	
	debug: true,

	viewport: ResponsiveBootstrapToolkit,

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
					},
					delay: 5000
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
			progress : {
				options: {
					icon: 'glyphicon glyphicon-time'
				},
				settings: {
					type: 'info',
					showProgressbar: true,
					allow_dismiss: false
				}
			},
		},
		ajax: {
			options: {
				url: 'ajax',
				method: 'GET',
				dataType: 'json'
			},
			data: {
				apikey: window.mylarAPIKey
			}			
		},
		table: {
			options: {
				theme : "bootstrap",
				widthFixed: true,
				headerTemplate : '{content} {icon}',

				widgets : [ "uitheme", "filter", "zebra" ],

			},
			widgetOptions : {
				zebra : ["even", "odd"],
				filter_reset : ".reset",
				filter_cssFilter: "form-control",
			}
		}
	},

	pubsub: _.extend({},Backbone.Events),
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
		$('[data-toggle="popover"]').popover();
		$('.responsive-tabs').responsiveTabs({
		  accordionOn: ['xs', 'sm'] // xs, sm, md, lg
		});
		$('div.btn-group[data-toggle-name]').each(function() {
		    var group   = $(this);
		    var form    = group.parents('form').eq(0);
		    var name    = group.attr('data-toggle-name');
		    var hidden  = $('input[name="' + name + '"]', form);
		    $('button', group).each(function(){
		      var button = $(this);
		      button.on('click', function(){
		        hidden.val($(this).val());
		        $('button',group).removeClass('active');
		        $(this).addClass('active');
		      });
		      if(button.val() == hidden.val()) {
		        button.addClass('active');
		      }
		    });
		  });
		
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
		if( arguments.length > 1 ){
			var customOptions  = $.extend(true,{},mylar.config.table.options, arguments[1])
		} else {
			var customOptions  = mylar.config.table.options;
		}
		if( arguments.length > 2 ){
			var customWidgetOptions  = $.extend(true,{},mylar.config.table.widgetOptions, arguments[2])
		} else {
			var customWidgetOptions  = mylar.config.table.widgetOptions;
		}
		
		customOptions.widgetOptions = customWidgetOptions;

		mylar.console.log( customOptions );

		target
		.tablesorter( customOptions )
		.tablesorterPager({
			container: $(".ts-pager"),
			cssGoto  : ".pagenum",
			removeRows: false,
			output: '{startRow} - {endRow} / {filteredRows} ({totalRows})'

		});
		return target;
	},
	notify: {
		info: function(message){
			var messageOptions = {},
				messageSettings = {};

			if( arguments.length > 1 ){
				var messageOptions  = $.extend(messageOptions,mylar.config.notify.info.options, arguments[1])
			} else {
				var messageOptions  = mylar.config.notify.info.options;
			}
			if( arguments.length > 2 ){
				var messageSettings = $.extend(messageSettings,mylar.config.notify.info.settings, arguments[2])
			} else {
				var messageSettings = mylar.config.notify.info.settings;
			}

			messageOptions.message = message;

			return mylar.notify.show( messageOptions, messageSettings );
		},
		success: function(message){
			var messageOptions = {},
				messageSettings = {};

			if( arguments.length > 1 ){
				var messageOptions  = $.extend(messageOptions, mylar.config.notify.success.options, arguments[1])
			} else {
				var messageOptions  = mylar.config.notify.success.options;
			}
			if( arguments.length > 2 ){
				var messageSettings = $.extend(messageSettings, mylar.config.notify.success.settings, arguments[2])
			} else {
				var messageSettings = mylar.config.notify.success.settings;
			}

			messageOptions.message = message;

			return mylar.notify.show( messageOptions, messageSettings );
		},
		warn: function(message){
			var messageOptions = {},
				messageSettings = {};

			if( arguments.length > 1 ){
				var messageOptions  = $.extend(messageOptions, mylar.config.notify.warn.options, arguments[1])
			} else {
				var messageOptions  = mylar.config.notify.warn.options;
			}
			if( arguments.length > 2 ){
				var messageSettings = $.extend(messageSettings, mylar.config.notify.warn.settings, arguments[2])
			} else {
				var messageSettings = mylar.config.notify.warn.settings;
			}

			messageOptions.message = message;

			return mylar.notify.show( messageOptions, messageSettings );
		},
		error: function(message){
			var messageOptions = {},
				messageSettings = {};

			if( arguments.length > 1 ){
				var messageOptions  = $.extend(messageOptions, mylar.config.notify.error.options, arguments[1])
			} else {
				var messageOptions  = mylar.config.notify.error.options;
			}
			if( arguments.length > 2 ){
				var messageSettings = $.extend(messageSettings, mylar.config.notify.error.settings, arguments[2])
			} else {
				var messageSettings = mylar.config.notify.error.settings;
			}

			messageOptions.message = message;

			return mylar.notify.show( messageOptions, messageSettings );
		},
		progress: function(message){
			var messageOptions = {},
				messageSettings = {};

			if( arguments.length > 1 ){
				var messageOptions  = $.extend(messageOptions, mylar.config.notify.progress.options, arguments[1])
			} else {
				var messageOptions  = mylar.config.notify.progress.options;
			}
			if( arguments.length > 2 ){
				var messageSettings = $.extend(messageSettings, mylar.config.notify.progress.settings, arguments[2])
			} else {
				var messageSettings = mylar.config.notify.progress.settings;
			}

			messageOptions.message = message;

			return mylar.notify.show( messageOptions, messageSettings );
		},
		show: function(options,settings){
			var messageOptions = {},
				messageSettings = {};

			$.extend(messageOptions,mylar.config.notify.default.options, options);
			$.extend(messageSettings, mylar.config.notify.default.settings, settings);
			
			if( mylar.debug ) mylar.console.log(messageOptions.message, messageOptions,messageSettings);
			return $.notify( messageOptions, messageSettings );
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

	},

	ajax: function(data){
		var ajaxOptions = mylar.config.ajax.options;
		var ajaxData = $.extend(mylar.config.ajax.data, data);
		
		ajaxOptions.data = ajaxData;

		if ( arguments.length > 1 ){
			ajaxOptions.success = arguments[1];
		} else {
			ajaxOptions.success = mylar.ajaxFunctions.success;
		}
		if ( arguments.length > 2 ){
			ajaxOptions.error = arguments[2];
		} else {
			ajaxOptions.error = mylar.ajaxFunctions.error;
		}

		return $.ajax( ajaxOptions );
	},

	ajaxFunctions: {
		success: function(data, status, jqXHR){

		},
		error: function(jqXHR, status, error){

		},
		complete: function(jqXHR, status){

		},
		beforeSend: function(jqXHR, settings){

		},

	},

	getCheckedIssues: function( tableSelector ){
		var data = {};
		$(tableSelector + ' tbody').find(':checked').each(function(){
			data[ $(this).attr('name') ] = $(this).val();
		});
		return data;
	}
});

mylar.init();
