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
		if( this.Status == 'Paused' ) this.isPaused = true;
		else if ( this.Status == 'Loading' ) this.isLoading = true;
		else if ( this.Status == 'Error' ) this.isError = true;
		else this.isActive = true;
		Backbone.Model.apply(this, arguments);
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
	}
});