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

mylar.collections = {};
mylar.pageableCollections = {};

mylar.collections.Comics = Backbone.Collection.extend({ model: mylar.models.comic });
mylar.comics = new mylar.collections.Comics();
if( initialData.hasOwnProperty( 'comics' ) ){
	mylar.comics.reset( initialData.comics );
}
mylar.pageableCollections.Comics = Backbone.PageableCollection.extend({
	model: mylar.models.comic,
	state: {
		sortKey: "ComicSortName"
	}
});


mylar.collections.Issues = Backbone.Collection.extend({ model: mylar.models.issue });
mylar.issues = new mylar.collections.Issues();
if( initialData.hasOwnProperty( 'issues' ) ){
	mylar.issues.reset( initialData.issues );
}



