var mylar = mylar || {};

mylar.models = {};

mylar.models.comic = Backbone.Model.extend({
	defaults: {
		ComicID       : 0,
		ComicImage    : "cache/default.jpg",
		ComicName     : "",
		ComicPublished:"",
		ComicPublisher:"",
		ComicSortName :"",
		ComicYear     :"",
		DateAdded     :"",
		LatestDate    :"",
		LatestIssue   :"",
		Status        :"",
		haveissues    :0,
		percent       :0,
		recentstatus  :"",
		totalissues   :0,
		
		isPaused      : false,
		isLoading     : false,
		isError       : false,
		isActive      : false
	},
	constructor: function(){
		Backbone.Model.apply(this, arguments);
		//console.log(this);
		if( this.Status == 'Paused' ) this.set("isPaused", true);
		else if ( this.Status == 'Loading' ) this.set("isLoading", true);
		else if ( this.Status == 'Error' ) this.set("isError", true);
		else this.set("isActive", true);
		this.set("publisherImage",mylar.utils.getPublisherImage( this.get("ComicPublisher") ));
	},
	generateCovers: function(){
		var startMsg = mylar.notify.info( 'Initiating cover image generation of ' + this.get('ComicName') );
		mylar.ajax({
			cmd: 'coverComposition',
			comicID: this.get('ComicID')
		}).fail(function(){
			mylar.notify.error( 'Could not generate cover images for ' + screen.comicdetails.comicName );
			startMsg.close();
		}).done(function(){
			mylar.notify.success( screen.comicdetails.comicName + ' cover images have been generated.' );
			startMsg.close();
		});
	}
});

mylar.models.issue = Backbone.Model.extend({
	defaults: {
		AltIssueNumber :null,
		ArtworkURL     :null,
		ComicID        :"",
		ComicName      :"",
		ComicSize      :"",
		DateAdded      :null,
		ImageURL       :"",
		ImageURL_ALT   :"",
		Int_IssueNumber:0,
		IssueDate      :"",
		IssueDate_Edit :null,
		IssueID        :"",
		IssueName      :"",
		Issue_Number   :"",
		Location       :"",
		ReleaseDate    :"",
		Status         :"",
		Type           :null,
		inCacheDIR     :null,

		IssueDateFormatted    : "",
		isDownloadedOrArchived: false,
		isSkipped             : false,
		isWanted              : false,
		isSnatched            : false,
		isDownloaded          : false,
		isArchived            : false,
		isIgnored             : false,
		isFailed              : false
	},
	constructor: function(){
		Backbone.Model.apply(this, arguments);
		
		if( 	 this.get("Status") == 'Skipped' )    this.set("isSkipped",true);
		else if( this.get("Status") == 'Wanted' )     this.set("isWanted",true);
		else if( this.get("Status") == 'Snatched' )   this.set("isSnatched",true);
		else if( this.get("Status") == 'Downloaded' ) this.set("isDownloaded",true);
		else if( this.get("Status") == 'Archived' )   this.set("isArchived",true);
		else if( this.get("Status") == 'Ignored' )    this.set("isIgnored",true);
		else if( this.get("Status") == 'Failed' )     this.set("isFailed",true);

		if( 	 this.get("Status") == "Downloaded" 
			  || this.get("Status") == "Archived")    this.set("isDownloadedOrArchived",true);

		var thisDate = moment( this.get("IssueDate"), "YYYY-MM-DD" )
		this.set("IssueDateFormatted", thisDate.format("MMM D, YYYY"))
	},
	generateCover: function(){
		var that = this;
		mylar.console.log('Generating Cover for Issue #',this.get("Issue_Number"));
		var startMsg = mylar.notify.info( 'Initiating cover image generation of ' + this.get('ComicName') );
		mylar.ajax({
			cmd: 'coverComposition',
			comicID: this.get('ComicID'),
			issueID: this.get('IssueID')
		}).fail(function(){
			mylar.notify.error( 'Could not generate cover images for Issue #' + that.get("Issue_Number") );
			startMsg.close();
		}).done(function(data){
			if( data.hasOwnProperty('success') ){
				mylar.notify.success( 'Cover image have been generated for Issue #' + that.get("Issue_Number") );
				startMsg.close();
				mylar.pubsub.trigger('issuecover:created', { IssueID: that.get('IssueID') });	
			} else {
				mylar.notify.warn( 'Cover image could not be generated for Issue #' + that.get("Issue_Number") );
				startMsg.close();
			}
			
		});
	}
});