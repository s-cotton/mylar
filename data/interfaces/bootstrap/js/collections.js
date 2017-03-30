var mylar = mylar || {};

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
mylar.pageableCollections.Issues = Backbone.PageableCollection.extend({
	model: mylar.models.issue,
	state: {
		sortKey: "IssueName"
	}
});

mylar.collections.selectedComics = Backbone.Collection.extend({
	model: mylar.models.comic,
	initialize: function(){
		mylar.pubsub.on("selection:comic:add", this.add, this);
		mylar.pubsub.on("selection:comic:remove", this.remove, this);
		mylar.pubsub.on("pager:resetView", this.clearSelected, this);
		this.on('add', this.broadcastAdd, this );
		this.on('remove', this.broadcastRemove, this );
	},
	isSelected: function( model ){
		//console.log(model,{ ComicID: model.attributes.ComicID },this.where({ ComicID: model.attributes.ComicID }).length);
		return ( this.where({ ComicID: model.attributes.ComicID }).length > 0 ) ? true : false;
	},
	clearSelected: function(broadcast){
		/*var that = this;
		this.each(function(model){
			that.remove( model, {silent: true} );
		});*/
		this.reset({silent: true});
		if( broadcast !== false ) this.broadcastSelection();
	},
	broadcastAdd: function(){
		this.broadcastSelection();
	},
	broadcastRemove: function(){
		this.broadcastSelection();
	},
	broadcastSelection: function(){
		mylar.pubsub.trigger( "selection:update", this.pluck("ComicID") );	
	}
});

mylar.collections.selectedIssues = Backbone.Collection.extend({
	model: mylar.models.issue,
	initialize: function(){
		mylar.pubsub.on("selection:issue:add", this.add, this);
		mylar.pubsub.on("selection:issue:remove", this.remove, this);
		mylar.pubsub.on("pager:resetView", this.clearSelected, this);
		this.on('add', this.broadcastAdd, this );
		this.on('remove', this.broadcastRemove, this );
	},
	isSelected: function( model ){
		return ( this.where({ IssueID: model.attributes.IssueID }).length > 0 ) ? true : false;
	},
	clearSelected: function(){
		this.reset();
	},
	broadcastAdd: function(){
		mylar.pubsub.trigger( "selection:issue:added", arguments );
	},
	broadcastRemove: function(){
		mylar.pubsub.trigger( "selection:issue:removed", arguments );
	}
});