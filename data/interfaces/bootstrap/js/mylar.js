var mylar = {
	
	pubsub: {},

	config: {},


	screens: [],
	urlData: [],
	configData: [],

	init: function(){
		$(document).ready( this.docReady );
		$(window).on( 'load', this.windowLoad );
		$(window).on( 'resize', this.windowResize );
		$(window).on( 'unload', this.windowUnload );
	},
	docReady: function(){},
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
	}
}

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