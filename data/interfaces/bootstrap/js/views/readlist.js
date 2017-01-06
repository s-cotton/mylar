var mylar = mylar || {};
var screen = screen || {};

screen.readlist = {

	thisScreen: this,

	init: function(){
		
	},

	docReady: function(){
		mylar.initTable( $('#bsIssuesTable') );

		/**
		 * Set up click handlers for various actions around page
		 */
		$('body').on( "click", ".sync-to-device", screen.readlist.syncFiles );
		$('body').on( "click", '.remove-read-from-list', screen.readlist.removeReadFromList );
		$('body').on( "click", '.force-new-check', screen.readlist.forceNewCheck );
		$('body').on( "click", '.clear-file-cache', screen.readlist.clearFileCache );
		$('body').on( "click", '.remove-from-read-list', screen.readlist.removeFromReadList );
		$('body').on( "click", '.mark-as-read', screen.readlist.markAsRead );
		$('body').on( "click", '.mark-all-as a', screen.readlist.markAllAs );
	},

	windowLoad: function(){},
	windowResize: function(){},
	windowUnload: function(){},

	removeFromReadList: function(){
		var issueID = $(this).parents('tr').data('issueid');
		var comicName = $(this).parents('tr').data('comicname');
		var issueNumber = $(this).parents('tr').data('issuenumber');

		var startMsg = mylar.notify.info('Removing ' + comicName + ' #' + issueNumber + ' from Reading List');
		mylar.ajax({
			cmd: 'removefromreadlist',
			IssueID: issueID
		}).fail(function(){
			mylar.notify.error('Could not remove ' + comicName + ' #' + issueNumber + ' from Reading List' );
			startMsg.close();
		}).done(function(){
			mylar.notify.success( 'Sucessfully removed ' + comicName + ' #' + issueNumber + ' from Reading List' );
			startMsg.close();
		});
	},
	markAsRead: function(){
		var issueID = $(this).parents('tr').data('issueid');
		var comicName = $(this).parents('tr').data('comicname');
		var issueNumber = $(this).parents('tr').data('issuenumber');

		var startMsg = mylar.notify.info('Marking ' + comicName + ' #' + issueNumber + ' as Read');
		mylar.ajax({
			cmd: 'markasRead',
			IssueID: issueID
		}).fail(function(){
			mylar.notify.error( 'Could not mark ' + comicName + ' #' + issueNumber + ' as Read' );
			startMsg.close();
		}).done(function(){
			mylar.notify.success( 'Successfully marked ' + comicName + ' #' + issueNumber + ' as Read' );
			startMsg.close();
		});
	},
	syncFiles: function( e ){
		var startMsg = mylar.notify.info('Starting Sync with Tablet');
		mylar.ajax({
			cmd: 'syncfiles',
		}).fail(function(){
			mylar.notify.error( 'Could not sync with tablet' );
			startMsg.close();
		}).done(function(){
			mylar.notify.success( 'Successfully started the tablet sync' );
			startMsg.close();
		});
	},
	removeReadFromList: function(){
		var startMsg = mylar.notify.info('Removing all read issues from Reading List');
		mylar.ajax({
			cmd: 'removefromreadlist',
			AllRead: 1
		}).fail(function(){
			mylar.notify.error( 'Could not remove all read from Reading List' );
			startMsg.close();
		}).done(function(){
			mylar.notify.success( 'Successfully removed all read from the Reading List' );
			startMsg.close();
		});
	},
	forceNewCheck: function(){
		var startMsg = mylar.notify.info('Forcing New Check');
		mylar.ajax({
			cmd: 'forcenewcheck',
			AllRead: 1
		}).fail(function(){
			mylar.notify.error( 'Could not Force New Check' );
			startMsg.close();
		}).done(function(){
			mylar.notify.success( 'Successfully Forced New Check' );
			startMsg.close();
		});
	},
	clearFileCache: function(){
		var startMsg = mylar.notify.info('Clearing File Cache');
		mylar.ajax({
			cmd: 'clearfilecache',
			AllRead: 1
		}).fail(function(){
			mylar.notify.error( 'Could not Clear File Cache' );
			startMsg.close();
		}).done(function(){
			mylar.notify.success( 'Successfully Cleared File Cache' );
			startMsg.close();
		});
	},
	markAllAs: function(){
		var thisAction = $(this).text();
		var selectedIssues = mylar.getCheckedIssues( '#bsIssuesTable' );
		var totalIssues = Object.keys(selectedIssues).length;

		if( totalIssues <= 0 ){
			mylar.notify.warn( 'No issues selected' );
		} else {
			var startMsg = mylar.notify.info( 'Marking ' + totalIssues + ' issues as ' + thisAction );

			mylar.ajax({
				cmd: 'markreads',
				action: thisAction,
				issues: mylar.getCheckedIssues( '#bsIssuesTable' )
			}).fail(function(){
				mylar.notify.error('Could not mark ' + totalIssues + ' issues as ' + thisAction );
				startMsg.close();
			}).done(function(){
				mylar.notify.success('Successfully marked ' + totalIssues + ' issues as ' + thisAction );
				startMsg.close();
			});
			/*doAjaxCall('markreads',$(this),'table',true);*/
		}
		
	},
}

mylar.registerScreen( screen.readlist, [
	'readlist'
], {
	ajax: true
});