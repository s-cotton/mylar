var mylar = mylar || {};
var screen = screen || {};

screen.history = {

	thisScreen: this,
	debug: true,

	init: function(){
		
	},

	docReady: function(){
		mylar.initTable( $('#bsIssuesTable') );

		/**
		 * Set up click handlers for various actions around page
		 */
		$('body').on( "click", ".clear-history", screen.history.clearhistory );

		$('body').on( "click", '.clear-all-history', screen.history.clearAllHistory );
		$('body').on( "click", '.clear-processed', screen.history.clearProcessed );
		$('body').on( "click", '.clear-unprocessed', screen.history.clearUnprocessed );
		$('body').on( "click", '.clear-snatched', screen.history.clearSnatched );
		$('body').on( "click", '.clear-nzblog', screen.history.clearNZBLOG );
		$('body').on( "click", '.mark-issues-as li > a', screen.history.markIssuesAs );

	},

	windowLoad: function(){},
	windowResize: function(){},
	windowUnload: function(){},

	clearAllHistory: function(){
		if( screen.history.debug ){
			doAjaxCall('clearhistory?type=all',$(this),'table');
		}
	},
	clearProcessed: function(){
		if( screen.history.debug ){
			doAjaxCall('clearhistory?type=Processed',$(this),'table');
		}
	},
	clearUnprocessed: function(){
		if( screen.history.debug ){
			doAjaxCall('clearhistory?type=Unprocessed',$(this),'table');
		}
	},
	clearSnatched: function(){
		if( screen.history.debug ){
			doAjaxCall('clearhistory?type=Snatched',$(this),'table');
		}
	},
	clearNZBLOG: function(){
		if( screen.history.debug ){
			doAjaxCall('wipenzblog',$(this),'table');
		}
	},
	markIssuesAs: function(){
		doAjaxCall('markissues',$(this),'table',true);
	},

}

mylar.registerScreen( screen.history, [
	'history'
], {
	ajax: true
});