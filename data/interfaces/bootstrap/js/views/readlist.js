var mylar = mylar || {};
var screen = screen || {};

screen.readlist = {

	thisScreen: this,

	init: function(){
		
	},

	docReady: function(){
		mylar.initTable( $('#bsIssuesTable') );
		$('.sync-to-device').click( screen.readlist.syncFiles );
		$('.remove-read-from-list').click( screen.readlist.removeReadFromList );
		$('.force-new-check').click( screen.readlist.forceNewCheck );
		$('.clear-file-cache').click( screen.readlist.clearFileCache );
		$('.remove-from-read-list').click( screen.readlist.removeFromReadList );
		$('.mark-as-read').click( screen.readlist.markAsRead );
	},

	windowLoad: function(){},
	windowResize: function(){},
	windowUnload: function(){},

	removeFromReadList: function(){
		var issueID = $(this).parents('tr').data('issueid');
		doAjaxCall('removefromreadlist?IssueID=' + issueID,$(this),'table');
	},
	markAsRead: function(){
		var issueID = $(this).parents('tr').data('issueid');
		doAjaxCall('markasRead?IssueID=' + issueID, $(this),'table');
	},
	syncFiles: function(){
		doAjaxCall('syncfiles',$(this),'table');
	},
	removeReadFromList: function(){
		doAjaxCall('removefromreadlist?AllRead=1',$(this),'table')
	},
	forceNewCheck: function(){},
	clearFileCache: function(){},
}

mylar.registerScreen( screen.readlist, [
	'readlist'
], {
	ajax: true
});