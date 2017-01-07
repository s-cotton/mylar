var mylar = mylar || {};
var screen = screen || {};

screen.comicdetails = {

	debug: true,

	thisScreen: this,
	comicID: false,
	comicName: false,
	comicLocation: false,

	init: function(){
		screen.comicdetails.comicID = $('[name="ComicID"]').val();
		screen.comicdetails.comicName = $('[name="ComicName"]').val();
		screen.comicdetails.comicLocation = $('[name="ComicLocation"]').val();
	},

	docReady: function(){
		mylar.initTable( $('#bsIssuesTable') );

		$( "body" ).on( "click", ".refresh-comic", screen.comicdetails.refreshComic );
		$( "body" ).on( "click", ".delete-comic", screen.comicdetails.deleteComic );
		$( "body" ).on( "click", ".rename-files", screen.comicdetails.renameFiles );
		$( "body" ).on( "click", ".recheck-files", screen.comicdetails.recheckFiles );
		$( "body" ).on( "click", ".retag-issues", screen.comicdetails.retagIssues );
		$( "body" ).on( "click", ".resume-comic", screen.comicdetails.resumeComic );
		$( "body" ).on( "click", ".pause-comic", screen.comicdetails.pauseComic );
		$( "body" ).on( "click", ".delete-annuals", screen.comicdetails.deleteAnnuals );
		$( "body" ).on( "click", ".add-all-to-readinglist", screen.comicdetails.addAllToReadingList );
		$( "body" ).on( "click", ".manual-search", screen.comicdetails.manualSearch );
		$( "body" ).on( "click", ".mark-issue-as-wanted", screen.comicdetails.markIssueAsWanted );
		$( "body" ).on( "click", ".mark-issue-as-skipped", screen.comicdetails.markIssueAsSkipped );
		$( "body" ).on( "click", ".retry-issue", screen.comicdetails.retryIssue );
		$( "body" ).on( "click", ".mark-issue-as-failed", screen.comicdetails.markIssueAsFailed );
		$( "body" ).on( "click", ".view-issue-details", screen.comicdetails.viewIssueDetails );
		$( "body" ).on( "click", ".manually-metatag-issue", screen.comicdetails.manuallyMetatagIssue );
		$( "body" ).on( "click", ".add-issue-to-reading-list", screen.comicdetails.addIssueToReadingList );
		$( "body" ).on( "click", ".retry-same-download", screen.comicdetails.retrySameDownload );
	},

	windowLoad: function(){},
	windowResize: function(){},
	windowUnload: function(){},

	refreshComic: function(event){
		var startMsg = mylar.notify.info( 'Initiating refresh of ' + screen.comicdetails.comicName );
		mylar.ajax({
			cmd: 'refreshSeries',
			IssueID: screen.comicdetails.comicID
		}).fail(function(){
			mylar.notify.error( 'Could not refresh ' + screen.comicdetails.comicName );
			startMsg.close();
		}).done(function(){
			mylar.notify.success( screen.comicdetails.comicName + ' is being refreshed.' );
			startMsg.close();
		});
		if( screen.comicdetails.debug ){
			doAjaxCall('refreshSeries?ComicID=' + screen.comicdetails.comicID, $(this), 'table' );	
		}	
	},

	deleteComic: function(event){
		bootbox.prompt({
			title: 'Delete Series Confirmation',
			inputType: 'checkbox',
			inputOptions: [
		        {
		            text: 'Remove directory when deleting Series? <span class="text-danger">THIS ACTION CAN NOT BE UNDONE</span>',
		            value: '2',
		        }
        	],
			callback: function(result){
				if( result !== null ) {
					if( result.length ){
						mylar.notify.info('Delete Confirmed, will delete folder');
					} else {
						mylar.notify.info('Delete Confirmed, will NOT delete folder');
					}
				}
			}
		});
	},

	renameFiles: function(event){
		var startMsg = mylar.notify.info( 'Initiating reanme of ' + screen.comicdetails.comicName + ' issue files' );
		mylar.ajax({
			cmd: 'manualRename',
			IssueID: screen.comicdetails.comicID
		}).fail(function(){
			mylar.notify.error( 'Could not rename ' + screen.comicdetails.comicName + ' issue files' );
			startMsg.close();
		}).done(function(){
			mylar.notify.success( screen.comicdetails.comicName + ' issue files are being refreshed.' );
			startMsg.close();
		});
		if( screen.comicdetails.debug ){
			doAjaxCall('manualRename?comicid=' + screen.comicdetails.comicID, $(this),'table')
		}	
	},

	recheckFiles: function(event){
		var startMsg = mylar.notify.info( 'Initiating recheck of ' + screen.comicdetails.comicName + ' issue files' );
		mylar.ajax({
			cmd: 'forceRescan',
			IssueID: screen.comicdetails.comicID
		}).fail(function(){
			mylar.notify.error( 'Could not recheck ' + screen.comicdetails.comicName + ' issue files' );
			startMsg.close();
		}).done(function(){
			mylar.notify.success( screen.comicdetails.comicName + ' issue files are being rechecked.' );
			startMsg.close();
		});
		if( screen.comicdetails.debug ){
			doAjaxCall('forceRescan?ComicID=' + screen.comicdetails.comicID, $(this),'table')
		}	
	},

	retagIssues: function(event){
		var startMsg = mylar.notify.info( 'Initiating retagging of ' + screen.comicdetails.comicName + ' issue files' );
		mylar.ajax({
			cmd: 'group_metatag',
			IssueID: screen.comicdetails.comicID
		}).fail(function(){
			mylar.notify.error( 'Could not retag ' + screen.comicdetails.comicName + ' issue files' );
			startMsg.close();
		}).done(function(){
			mylar.notify.success( screen.comicdetails.comicName + ' issue files are being retagged.' );
			startMsg.close();
		});
		if( screen.comicdetails.debug ){
			doAjaxCall('group_metatag?ComicID=' + screen.comicdetails.comicID + '&dirName=' + encodeURIComponent(screen.comicdetails.comicLocation), $(this),'table')
		}
	},

	resumeComic: function(event){
		var startMsg = mylar.notify.info( 'Initiating resume of ' + screen.comicdetails.comicName );
		mylar.ajax({
			cmd: 'resumeSeries',
			IssueID: screen.comicdetails.comicID
		}).fail(function(){
			mylar.notify.error( 'Could not resume ' + screen.comicdetails.comicName );
			startMsg.close();
		}).done(function(){
			mylar.notify.success( screen.comicdetails.comicName + ' has been resumed.' );
			startMsg.close();
		});
		if( screen.comicdetails.debug ){
			doAjaxCall('resumeSeries?ComicID=' + screen.comicdetails.comicID,$(this),true);
		}
	},

	pauseComic: function(event){
		var startMsg = mylar.notify.info( 'Initiating pause of ' + screen.comicdetails.comicName );
		mylar.ajax({
			cmd: 'pauseSeries',
			IssueID: screen.comicdetails.comicID
		}).fail(function(){
			mylar.notify.error( 'Could not pause ' + screen.comicdetails.comicName );
			startMsg.close();
		}).done(function(){
			mylar.notify.success( screen.comicdetails.comicName + ' has been paused.' );
			startMsg.close();
		});
		if( screen.comicdetails.debug ){
			doAjaxCall('pauseSeries?ComicID=' + screen.comicdetails.comicID,$(this),true)
		}
	},

	deleteAnnuals: function(event){
		bootbox.confirm("Are you sure you want to delete the annuals records from this comic series?",function(result){
			if( result ){
				window.location = 'annualDelete?comicid=' + screen.comicdetails.comicID
			}
		});
	},

	addAllToReadingList: function(event){
		var issues = [];
		$('a.add-issue-to-reading-list').each(function(){
			issues.push( {
				issueid: $(this).parents('tr').eq(0).data('issueid'),
				issuenumber: $(this).parents('tr').eq(0).data('issuenumber'),
			});
		});
		var totalIssues = issues.length;
		var stepSize = 100 / totalIssues;
		var currentStep = 0;
		
		if( totalIssues > 0 ){
			var progressMsg = mylar.notify.progress("Adding " + issues.length + " issues to watchlist");
			var issuesInterval = setInterval(function(){
				var currentIssue = issues.shift();
				if( typeof currentIssue == "undefined" ){
					clearInterval(issuesInterval);
					progressMsg.close();
					mylar.notify.success("Successfully added " + totalIssues + " to the read list.");
				} else {
					progressMsg.update("progress", Math.floor(currentStep) );
					mylar.ajax({
						cmd: 'addtoreadlist',
						issueID: currentIssue.issueid
					}).fail(function(){

					}).done(function(){
						currentStep = currentStep + stepSize;
					});
				}
			},250);
		} else {
			mylar.notify.warn("No issues to add to read list");
		}
	},

	manualSearch: function(event){
		var issueNumber = $(this).parents('tr').eq(0).data('issuenumber');
		var issueID = $(this).parents('tr').eq(0).data('issueid');
		var issueDate = $(this).parents('tr').eq(0).data('issuedate');

		var startMsg = mylar.notify.info( 'Initiating manual search for ' + screen.comicdetails.comicName + ' #' + issueNumber );
		mylar.ajax({
			cmd: 'queueit',
			ComicID: screen.comicdetails.comicID,
			IssueID: issueID,
			ComicIssue: issueNumber,
			ComicYear: issueDate,
			mode: 'want',
			manualsearch: 'True'
		}).fail(function(){
			mylar.notify.error( 'Could not manually search for ' + screen.comicdetails.comicName + ' #' + issueNumber );
			startMsg.close();
		}).done(function(){
			mylar.notify.success( 'Manually searching for ' + screen.comicdetails.comicName + ' #' + issueNumber );
			startMsg.close();
		});
		if( screen.comicdetails.debug ){
			doAjaxCall('queueit?ComicID=' + screen.comicdetails.comicID + '&IssueID=' + issueID + '&ComicIssue=' + issueNumber + '&ComicYear=' + issueDate + '&mode=want&manualsearch=True',$(this),'table')
		}
	},

	markIssueAsWanted: function(event){
		var issueNumber = $(this).parents('tr').eq(0).data('issuenumber');
		var issueID = $(this).parents('tr').eq(0).data('issueid');
		var issueDate = $(this).parents('tr').eq(0).data('issuedate');

		var startMsg = mylar.notify.info( 'Initiating status change for ' + screen.comicdetails.comicName + ' #' + issueNumber );
		mylar.ajax({
			cmd: 'queueit',
			ComicID: screen.comicdetails.comicID,
			IssueID: issueID,
			ComicIssue: issueNumber,
			ComicYear: issueDate,
			mode: 'want'
		}).fail(function(){
			mylar.notify.error( 'Could not mark ' + screen.comicdetails.comicName + ' #' + issueNumber + ' as wanted' );
			startMsg.close();
		}).done(function(){
			mylar.notify.success( screen.comicdetails.comicName + ' #' + issueNumber + ' marked as wanted' );
			startMsg.close();
		});
		if( screen.comicdetails.debug ){
			doAjaxCall('queueit?ComicID=' + screen.comicdetails.comicID + '&IssueID=' + issueID + '&ComicIssue=' + issueNumber + '&ComicYear=' + issueDate + '&mode=want',$(this),'table');
		}
	},

	markIssueAsSkipped: function(event){
		var issueNumber = $(this).parents('tr').eq(0).data('issuenumber');
		var issueID = $(this).parents('tr').eq(0).data('issueid');
		var issueDate = $(this).parents('tr').eq(0).data('issuedate');

		var startMsg = mylar.notify.info( 'Initiating status change for ' + screen.comicdetails.comicName + ' #' + issueNumber );
		mylar.ajax({
			cmd: 'unqueueissue',
			ComicID: screen.comicdetails.comicID,
			IssueID: issueID
		}).fail(function(){
			mylar.notify.error( 'Could not mark ' + screen.comicdetails.comicName + ' #' + issueNumber + ' as skipped' );
			startMsg.close();
		}).done(function(){
			mylar.notify.success( screen.comicdetails.comicName + ' #' + issueNumber + ' marked as skipped' );
			startMsg.close();
		});
		if( screen.comicdetails.debug ){
			doAjaxCall('unqueueissue?IssueID=' + issueID + '&ComicID=' + screen.comicdetails.comicID,$(this),'table');
		}
	},

	markIssueAsFailed: function(event){
		var issueNumber = $(this).parents('tr').eq(0).data('issuenumber');
		var issueID = $(this).parents('tr').eq(0).data('issueid');
		var issueDate = $(this).parents('tr').eq(0).data('issuedate');

		var startMsg = mylar.notify.info( 'Initiating status change for ' + screen.comicdetails.comicName + ' #' + issueNumber );
		mylar.ajax({
			cmd: 'unqueueissue',
			ComicID: screen.comicdetails.comicID,
			IssueID: issueID,
			mode: 'failed'
		}).fail(function(){
			mylar.notify.error( 'Could not mark ' + screen.comicdetails.comicName + ' #' + issueNumber + ' as failed' );
			startMsg.close();
		}).done(function(){
			mylar.notify.success( screen.comicdetails.comicName + ' #' + issueNumber + ' marked as failed' );
			startMsg.close();
		});
		if( screen.comicdetails.debug ){
			doAjaxCall('unqueueissue?IssueID=' + issueID + '&ComicID=' + screen.comicdetails.comicID+'&mode=failed',$(this),'table');
		}
	},

	retryIssue: function(event){
		var issueNumber = $(this).parents('tr').eq(0).data('issuenumber');
		var issueID = $(this).parents('tr').eq(0).data('issueid');
		var issueDate = $(this).parents('tr').eq(0).data('issuedate');

		var startMsg = mylar.notify.info( 'Initiating download retry for ' + screen.comicdetails.comicName + ' #' + issueNumber );
		mylar.ajax({
			cmd: 'retryit',
			ComicName: screen.comicdetails.comicName,
			ComicID: screen.comicdetails.comicID,
			IssueID: issueID,
			IssueNumber: issueNumber,
			ComicYear: issueDate
		}).fail(function(){
			mylar.notify.error( 'Could not retry the download for ' + screen.comicdetails.comicName + ' #' + issueNumber );
			startMsg.close();
		}).done(function(){
			mylar.notify.success( 'The download for ' + screen.comicdetails.comicName + ' #' + issueNumber + ' has been retried' );
			startMsg.close();
		});
		if( screen.comicdetails.debug ){
			doAjaxCall('retryit?ComicName=' + encodeURIComponent( screens.comicdetails.comicName ) + '&ComicID=' + screen.comicdetails.comicID + '&IssueID=' + issueID + '&IssueNumber=' + issueNumber + '&ComicYear=' + issueDate + '', $(this),'table');
		}		
	},

	viewIssueDetails: function(event){
	
	},

	manuallyMetatagIssue: function(event){
	
	},

	addIssueToReadingList: function(event){
	
	},

	retrySameDownload: function(event){

	},

}

mylar.registerScreen( screen.comicdetails, [
	'comicdetails'
], {
	ajax: true
});