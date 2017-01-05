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
		$('.mark-all-as a').click( screen.readlist.markAllAs );
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
	syncFiles: function(){
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
	forceNewCheck: function(){},
	clearFileCache: function(){},
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

	getCheckedIssues: function(){
		var data = {};
		$('#bsIssuesTable tbody').find(':checked').each(function(){
			data[ $(this).attr('name') ] = $(this).val();
		});
		return data;
	}
}

mylar.registerScreen( screen.readlist, [
	'readlist'
], {
	ajax: true
});