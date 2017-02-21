var mylar = mylar || {};
var screen = screen || {};

screen.logs = {

	thisScreen: this,
	debug: true,

	init: function(){
		
	},

	docReady: function(){
		mylar.initTable( $('#bsIssuesTable') );

		/**
		 * Set up click handlers for various actions around page
		 */
		$('body').on( "click", ".clear-logs", screen.logs.clearLogs );

		
		
	},

	windowLoad: function(){},
	windowResize: function(){},
	windowUnload: function(){},

	clearLogs: function(){
		startMsg = mylar.notify.info("Initiating Log Clear...");
		mylar.ajax({
			cmd: 'clearLogs'
		}).fail(function(){
			mylar.notify.error("Failed to clear logs");
			startMsg.close();
		}).done(function(){
			mylar.notify.success("All logs cleared");
			startMsg.close();
		});

		if( screen.logs.debug ){
			doAjaxCall('clearLogs',$(this),'table')	
		}		
	},
}

mylar.registerScreen( screen.logs, [
	'logs'
], {
	ajax: true
});