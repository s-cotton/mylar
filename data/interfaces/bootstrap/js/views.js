var mylar = mylar || {};

mylar.views = mylar.views || {};

mylar.views.comicPagerAndFilter = Backbone.View.extend({
	el: '.comic-pager',

	template: Handlebars.compile( $('#comic-pager-and-filter').html() ),

	context: "comics",
	actions: [],
	selectable: [],
	views: [],

	defaults: {
		comics: {
			sortBy: "ComicSortName"
		},
		issues: {
			sortBy: ""
		}
	},

	totalPages: 0,
	perPage: 16,
	sortBy: "ComicSortName",
	sortDir: 1,
	searchValue: "",

	currentPage: 1,
	
	events: {
		"click .change-page-size"	: "changePageSize",
		"click .change-sort-by"		: "changeSortBy",
		"keyup [name='search']"		: "filterComics",
		"click .reset-search"		: "resetSearch",
		"click .change-layout"		: "changeView"
	},
	initialize: function(){
		
	},

	render: function(){
		var templateData = this.dataObj();
		this.$el.html( this.template( templateData ) );
		this.setupPagination();
		mylar.pubsub.on('pager:updateState', this.updateState,this );
	},

	setContext: function(context){
		this.context = context;
	},

	setActions: function(actions){
		this.actions = actions;
	},

	setSelectable: function(selectable){
		this.selectable = selectable;
	},

	setViews: function(views){
		this.views = views;
	},

	updateState: function(data){
		var updatePager = false;
		if( this.totalPages != data.totalPages || this.currentPage != data.currentPage ) updatePager = true;
		this.totalPages = data.totalPages;
		this.currentPage = data.currentPage;
		if( updatePager ) this.setupPagination();
	},
	
	dataObj: function(){
		return {
			perpage: this.getPerPage(),
			views: this.views,
			selectable: this.selectable,
			actions: this.actions
		}
	},

	stateObj: function(){
		return {
			searchValue: this.searchValue,
			sortBy     : this.sortBy,
			sortDir    : this.sortDir,
			currentPage: this.currentPage > 0 ? this.currentPage : 1,
			perPage    : this.perPage,
		}
	},

	getPerPage: function(){
		var sizes = [];
		if( mylar.viewport.is('lg') || mylar.viewport.is('md') ){
			sizes = [
				{ count: 8 },
				{ count: 16, default: true },
				{ count: 32 },
				{ count: 64 },
				{ count: "All" }
			];
		} else if ( mylar.viewport.is('sm') || mylar.viewport.is('xs') ){
			sizes = [
				{ count: 10 },
				{ count: 20, default: true },
				{ count: 40 },
				{ count: 80 },
				{ count: "All" }
			];
		}
		return sizes;
	},

	setupPagination: function(){
		var that = this;
		this.$el.find('.pagination').twbsPagination("destroy");
		if( this.totalPages > 0 ){
			this.$el.find('.pagination').twbsPagination({
		        totalPages: this.totalPages,
		        visiblePages: 15,
		        startPage: this.currentPage,
		        onPageClick: function(event,page){
		        	if( that.currentPage != page ){
		        		that.changePage(page);	
		        	}
		        }
		    });	
		}		
	},

	changePage: function(page){
		this.currentPage = page;
		mylar.pubsub.trigger( 'pager:changePage', this.stateObj() );
	},

	changePageSize: function(e){
		$(e.target).parents('ul').eq(0).find('.active').removeClass('active');
		$(e.target).addClass('active');
		this.perPage = $(e.target).data('perpage');
		mylar.pubsub.trigger( 'pager:changePerPage', this.stateObj() );
		//this.setupPagination();
	},

	changeSortBy: function(e){
		$(e.target).parents('ul').eq(0).find('.active').removeClass('active');
		$(e.target).addClass('active');
		var sortBy = $(e.target).data('sortby');

		if( sortBy != this.sortBy ){
			this.sortBy = sortBy;
			this.sortDir = 1;
		} else {
			this.sortDir = this.sortDir * -1;
		}		
		mylar.pubsub.trigger( 'pager:sortBy', this.stateObj() );
	},

	filterComics: function(){
		if( this.searchValue.length == 0 ){ 
			this.currentPage = 1; 
		}
		this.searchValue = this.$el.find('[name="search"]').val();
		mylar.pubsub.trigger( 'pager:changeSearch', this.stateObj() );
	},

	resetSearch: function(){
		this.$el.find('[name="search"]').val('');
		this.searchValue = '';
		this.sortBy = "ComicSortName";
		this.sortDir = 1;
		this.currentPage = 1;
		this.perPage = 16;
		mylar.pubsub.trigger( 'pager:resetView', this.stateObj());
		this.setupPagination();
	},

	changeView: function(e){
		this.layout = $(e.target).attr('value');
		console.log(e.target);
		$(e.target).parents('.btn-group').eq(0).find('.active').removeClass('active');
		$(e.target).addClass('active');
		mylar.pubsub.trigger( 'pager:changeView', this.stateObj() );
	}

});

mylar.views.comicCoverBrowser = Backbone.View.extend({
	el: '.cover-browser',
	template: Handlebars.compile( $('#cover-gallery-container').html() ),
	collection: null,
	pager: null,
	covers: [],
	perPage: 16,
	sortBy: "ComicSortName",
	sortDir: 1,
	searchValue: "",

	currentPage: 1,
	
	events: {
		"click .change-page-size"	: "changePageSize",
		"click .change-sort-by"		: "changeSortBy",
		"keyup [name='search']"		: "filterComics",
		"click .reset-search"		: "resetSearch"
	},
	initialize: function(){
		this.setCollection();
		this.render();

		mylar.pubsub.on('pager:resetView pager:changeSearch pager:sortBy pager:changePage pager:changePerPage', this.updateView, this );
		
	},

	updateState: function(pagerData){
		console.log(pagerData);
		var that = this;
		
		if( this.searchValue.length > 0 || this.searchValue != pagerData.searchValue ){
			this.searchValue 	= pagerData.searchValue;
			this.setCollection();
		}
		if( pagerData.sortBy != this.sortBy || pagerData.sortDir != this.sortDir ){
			this.sortBy     	= pagerData.sortBy;
			this.sortDir    	= pagerData.sortDir;
			this.collection.setSorting( this.sortBy, this.sortDir, {full: true} );
			this.collection.comparator = function(model){ return model.get( that.sortBy ).toLowerCase(); };
			this.collection.sort();
		}
		
		this.currentPage	= pagerData.currentPage;
		if( pagerData.perPage != this.perPage ){
			this.perPage    	= pagerData.perPage;
		}
		
	},

	setCollection: function(){
		var that = this;
		if( this.searchValue.length ){
			this.collection = new mylar.pageableCollections.Comics( mylar.comics.filterValues( this.searchValue.toLowerCase() ),{
				mode: "client",
				comparator: function (model) { return model.get( that.sortBy ).toLowerCase(); },
			});
		} else {
			this.collection = new mylar.pageableCollections.Comics( initialData.comics,{
				mode: "client",
				comparator: function (model) { return model.get( that.sortBy ).toLowerCase(); },
			});
		}
		this.collection.setPageSize( this.perPage );
		
	},

	updateView: function(pagerData){
		this.updateState(pagerData);
		this.renderCovers();
	},

	setPageSize: function(pageSize){
		if( pageSize == "All" ){
			this.collection.setPageSize( this.collection.fullCollection.length );
		} else {
			this.collection.setPageSize( pageSize );	
		}	
	},

	render: function(){
		var that = this;

		var templateData = this.dataObj();
		this.$el.html( this.template( templateData ) );

		this.renderCovers();
		mylar.pubsub.trigger('pager:updateState', { currentPage: this.currentPage, totalPages: this.collection.state.totalPages });
		
		return this;
	},

	renderCovers: function(){
		this.$el.find('.covers').empty();
		
		this.setPageSize(this.perPage);
		if( this.currentPage > this.collection.state.totalPages ){
			this.currentPage = this.collection.state.totalPages;
		}

		this.collection.getPage( this.currentPage );

		for( var single_model in this.collection.models ){
			var thisCover = new mylar.views.comicCover({ model: this.collection.models[ single_model ] });
			this.$el.find('.covers').append( thisCover.render() );
		}
		this.setClearfix();

		mylar.pubsub.trigger('pager:updateState', { currentPage: this.currentPage, totalPages: this.collection.state.totalPages });
		
	},

	dataObj: function(){
		return {
			
		}
	},

	setClearfix: function(){
		this.$el.find('.row > .cover:nth-of-type(4n)').after('<div class="clearfix visible-md-block visible-lg-block"></div>');
		this.$el.find('.row > .cover:nth-of-type(2n)').after('<div class="clearfix visible-sm-block"></div>');
	}
});

mylar.views.comicCover = Backbone.View.extend({
	tagName: 'div',
	className: 'col-xs-12 col-sm-6 col-md-3 cover',
	model: mylar.models.comic,
	template: Handlebars.compile( $('#cover-gallery-single-cover').html() ),
	events: {
		'click .checked-issue' : 'checkIssue'
	},
	initialize: function(){
		//this.render()
	},
	render: function(){
		this.$el.html( this.template( this.model.toJSON() ) );
		return this.$el;
	},
	checkIssue: function(){
		if( this.$el.find('.checked-issue .glyphicon').hasClass('glyphicon-unchecked') ){
			this.$el.find('input[type="checkbox"]').attr('checked','checked');
			this.$el.find('.checked-issue .glyphicon').removeClass('glyphicon-unchecked')
			this.$el.find('.checked-issue .glyphicon').addClass('glyphicon-check')
		} else {
			this.$el.find('input[type="checkbox"]').removeAttr('checked');
			this.$el.find('.checked-issue .glyphicon').addClass('glyphicon-unchecked')
			this.$el.find('.checked-issue .glyphicon').removeClass('glyphicon-check')
		}
	}
})