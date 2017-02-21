var mylar = mylar || {};

mylar.views = mylar.views || {};

mylar.views.comicPagerAndFilter = Backbone.View.extend({
	el: '.comic-pager',

	template: Handlebars.compile( $('#comic-pager-and-filter').html() ),

	context: "comics",
	actions: [],
	selectable: [],
	views: [],
	sortable: [],
	searchable: [],

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
	layout: "",
	selected: [],

	searchTimeout: null,
	searchTimeoutDelay: 750,


	currentPage: 1,
	
	events: {
		"click .change-page-size"	: "changePageSize",
		"click .change-sort-by"		: "changeSortBy",
		"keyup [name='search']"		: "filterComics",
		"click .reset-search"		: "resetSearch",
		"click .change-layout"		: "changeLayout",
		"click .change-selected"	: "changeSelected",
		"click .mark-selected"		: "markSelected"
	},

	initialize: function(){
		
	},

	render: function(){
		var templateData = this.dataObj();
		this.$el.html( this.template( templateData ) );
		this.setupPagination();
		mylar.pubsub.on('pager:updateState', this.updateState,this );
		this.$el.find('[data-toggle="popover"]').popover();
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
		for( var i in this.views ){
			if( this.views[i].default ){
				this.layout = this.views[i].key;
			}
		}
	},

	setSortable: function(sortable){
		this.sortable = sortable;
	},

	setSearchable: function(searchable){
		this.searchable = searchable;
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
			actions: this.actions,
			sortable: this.sortable,
			searchable: this.searchable
		}
	},

	stateObj: function(){
		return {
			searchValue: this.searchValue,
			sortBy     : this.sortBy,
			sortDir    : this.sortDir,
			currentPage: this.currentPage > 0 ? this.currentPage : 1,
			perPage    : this.perPage,
			layout 	   : this.layout,
			selected   : this.selected //this.getSelectable()
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

	getSelectable: function(){
		if( this.selected.indexOf('all') >= 0 ){
			return [ 'all' ];
		} else {
			var selectable = [];
			for( var i in this.selectable ){
				if( this.selected.indexOf( this.selectable[i].key) >= 0 ){
					selectable.push( this.selectable[i].target );
				}
			}
			return selectable;
		}
		
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
		console.log($(e.target).data('sortby'));
		$(e.target).parents('ul').eq(0).find('.active').removeClass('active');
		$(e.target).addClass('active');
		var sortBy = false;

		for( var i in this.sortable ){
			if( this.sortable[i].key == $(e.target).data('sortby') ){
				sortBy = this.sortable[i].target;
			}
		}
		if( sortBy !== false ){
			if( sortBy != this.sortBy ){
				this.sortBy = sortBy;
				this.sortDir = 1;
			} else {
				this.sortDir = this.sortDir * -1;
			}		
			mylar.pubsub.trigger( 'pager:sortBy', this.stateObj() );
		}
	},

	filterComics: function( searchValue ){
		var that = this;
		if( this.searchValue.length == 0 ){ 
			this.currentPage = 1; 
		}
		this.searchValue = this.$el.find('[name="search"]').val();
		this.searchTimeout = setTimeout(function(){
			that.parseSearchValue();
		},this.searchTimeoutDelay);
	},

	parseSearchValue: function(){
		var split = this.searchValue.reduceWhiteSpace().explode(" ");
		console.log(split);
		var searchAttributes = {
			any: []
		};
		for( var split_i in split ){
			var thisSearchValue = split[ split_i ];
			if( thisSearchValue.indexOf("::") >= 0 ){
				thisSearchValueSplit = thisSearchValue.split("::");
				if( ! searchAttributes.hasOwnProperty(thisSearchValueSplit[0]) ){
					searchAttributes[ thisSearchValueSplit[0] ] = [];
				}
				searchAttributes[ thisSearchValueSplit[0] ].push( thisSearchValueSplit[1] );
			} else {
				searchAttributes.any.push( thisSearchValue );
			}
		}
		console.log(searchAttributes);

		//mylar.pubsub.trigger( 'pager:changeSearch', this.stateObj() );	
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

	changeLayout: function(e){
		this.layout = $(e.target).attr('value');
		$(e.target).parents('.btn-group').eq(0).find('.active').removeClass('active');
		$(e.target).addClass('active');
		mylar.pubsub.trigger( 'pager:changeLayout', this.stateObj() );
	},

	setInitialLayout: function(){
		mylar.pubsub.trigger( 'pager:changeLayout', this.stateObj() );
	},

	changeSelected: function(e){
		if( $(e.currentTarget).data('selectable') == 'clear' ){
			this.selected = [];	
		} else if ( $(e.currentTarget).data('selectable') == 'all' ){
			this.selected = [];
			this.selected.push( 'all' );
		} else {
			if( this.selected.indexOf('all') >= 0 ){
				this.selected.splice( this.selected.indexOf( 'all' ), 1);
			}
			if( $(e.target).hasClass('active') ){
				$(e.target).removeClass('active');
				this.selected.splice( this.selected.indexOf( $(e.target).data('selectable') ), 1);
			} else {
				$(e.target).addClass('active');
				this.selected.push( $(e.target).data('selectable') );
			}	
		}		
		mylar.pubsub.trigger( 'pager:changeSelected', this.stateObj() );
	},

	markSelected: function(e){
		mylar.pubsub.trigger( 'mark:selected', $(e.target).data('action') );
	},

});

mylar.views.comicBrowser = Backbone.View.extend({
	
	collection: null,
	layout: false,
	covers: [],

	perPage: 16,
	sortBy: "ComicSortName",
	sortDir: 1,
	searchValue: "",
	currentPage: 1,
	actions: [],
	
	initialize: function(){
		this.setCollection();
		//this.render();

		mylar.pubsub.on('pager:resetView pager:changeSearch pager:sortBy pager:changePage pager:changePerPage pager:changeLayout', this.updateView, this );
	},

	setActions: function(actions){
		this.actions = actions;
	},

	updateView: function(pagerData){
		this.updateState(pagerData);
		this.renderItems();
	},

	updateState: function(pagerData){
		//console.log(pagerData);
		var that = this;
		
		if( this.searchValue.length > 0 || this.searchValue != pagerData.searchValue ){
			this.searchValue 	= pagerData.searchValue;
			this.setCollection();
		}
		if( pagerData.sortBy != this.sortBy || pagerData.sortDir != this.sortDir ){
			//console.log('Updating Sort',pagerData.sortBy,pagerData.sortDir);
			this.sortBy     	= pagerData.sortBy;
			this.sortDir    	= pagerData.sortDir;
			if( this.sortDir > 0 ){
				this.collection.setSorting( this.sortBy, this.sortDir, {full: true} );	
			} else {
				this.collection.setSorting( this.sortBy, {full: true} );
			}
			
			this.collection.comparator = function(model){ return model.get( that.sortBy ); };
			this.collection.fullCollection.sort();
		}
		
		this.currentPage	= pagerData.currentPage;
		if( pagerData.perPage != this.perPage ){
			this.perPage    	= pagerData.perPage;
		}

		if( pagerData.layout == this.layout ){
			this.$el.removeClass('hidden');
		} else {
			this.$el.addClass('hidden');
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

		this.renderItems();
		mylar.pubsub.trigger('pager:updateState', { currentPage: this.currentPage, totalPages: this.collection.state.totalPages });
		
		return this;
	},

	dataObj: function(){
		return {
			
		}
	}
});

mylar.views.comicGridBrowser = mylar.views.comicBrowser.extend({
	el: '.grid-browser',
	template: Handlebars.compile( $('#cover-grid-container').html() ),
	
	layout: 'grid',

	renderItems: function(){
		this.$el.find('.covers').empty();
		
		this.setPageSize(this.perPage);
		if( this.currentPage > this.collection.state.totalPages ){
			this.currentPage = this.collection.state.totalPages;
		}

		this.collection.getPage( this.currentPage );

		for( var single_model in this.collection.models ){
			var thisCover = new mylar.views.comicCover({ model: this.collection.models[ single_model ], actions: this.actions });
			thisCover.setActions( this.actions );
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
		this.$el.find('.row > .cover:nth-of-type(12n)').after('<div class="clearfix visible-xl-block"></div>');
		this.$el.find('.row > .cover:nth-of-type(6n)').after('<div class="clearfix visible-lg-block"></div>');
		this.$el.find('.row > .cover:nth-of-type(4n)').after('<div class="clearfix visible-md-block"></div>');
		this.$el.find('.row > .cover:nth-of-type(3n)').after('<div class="clearfix visible-sm-block"></div>');
		this.$el.find('.row > .cover:nth-of-type(2n)').after('<div class="clearfix visible-xs-block"></div>');
	}
});

mylar.views.comicCoverBrowser = mylar.views.comicBrowser.extend({
	el: '.cover-browser',
	template: Handlebars.compile( $('#cover-flow-container').html() ),
	
	layout: 'covers',
	initFlipster: false,

	renderItems: function(){
		var templateData = this.dataObj();
		this.$el.html( this.template( templateData ) );
		this.$el.find('.cover-flow > ul').empty();
		//if( this.initFlipster ) this.$el.find('.cover-flow').flipster('index');
		this.setPageSize(this.perPage);
		if( this.currentPage > this.collection.state.totalPages ){
			this.currentPage = this.collection.state.totalPages;
		}

		this.collection.getPage( this.currentPage );

		for( var single_model in this.collection.models ){
			var thisCover = new mylar.views.comicFlowCover({ model: this.collection.models[ single_model ], actions: this.actions });
			thisCover.setActions( this.actions );
			this.$el.find('.cover-flow > ul').append( thisCover.render() );
		}
		this.setCoverFlow();

		mylar.pubsub.trigger('pager:updateState', { currentPage: this.currentPage, totalPages: this.collection.state.totalPages });
		
	},

	dataObj: function(){
		return {
			
		}
	},

	setCoverFlow: function(){
		this.$el.find('.cover-flow').flipster({
			start: 0
		});
	}
});

mylar.views.comicTableBrowser = mylar.views.comicBrowser.extend({
	el: '.table-browser',
	template: Handlebars.compile( $('#table-browser-container').html() ),

	layout: 'list',
	
	renderItems: function(){
		console.log('Rendering Comic Rows');
		this.$el.find('tbody').empty();
		
		this.setPageSize(this.perPage);
		if( this.currentPage > this.collection.state.totalPages ){
			this.currentPage = this.collection.state.totalPages;
		}

		this.collection.getPage( this.currentPage );

		for( var single_model in this.collection.models ){
			var thisRow = new mylar.views.comicRow({ model: this.collection.models[ single_model ], actions: this.actions });
			thisRow.setActions( this.actions );
			this.$el.find('tbody').append( thisRow.render() );
		}

		mylar.pubsub.trigger('pager:updateState', { currentPage: this.currentPage, totalPages: this.collection.state.totalPages });
		
	},

	dataObj: function(){
		return {
			
		}
	},

});

mylar.views.comicFlowCover = Backbone.View.extend({
	tagName: 'li',
	model: mylar.models.comic,
	template: Handlebars.compile( $('#cover-gallery-single-cover').html() ),
	actions: [],
	events: {
		'click .checked-comic' : 'checkComic',
		'click .mark-comic'	   : 'markComic',
	},
	initialize: function(){
		//this.render()
		mylar.pubsub.on('selection:update', this.maybeRender, this)
	},
	setActions: function(actions){
		this.actions = actions;
	},
	maybeRender: function( models ){
		this.render();
	},
	render: function(){
		var templateData = _.extend(this.model.toJSON(), {
			'selected': mylar.selectedComics.isSelected( this.model ),
			actions: this.actions
		});
		//console.log(templateData);
		this.$el.html( this.template( templateData ) );
		this.$el.find('.panel-title a').css('width', this.$el.find('.panel-body > img').width() )
		return this.$el;
	},
	checkComic: function(){
		if( this.$el.find('.checked-comic .glyphicon').hasClass('glyphicon-unchecked') ){
			this.$el.find('.checked-comic .glyphicon').removeClass('glyphicon-unchecked')
			this.$el.find('.checked-comic .glyphicon').addClass('glyphicon-check')
			mylar.pubsub.trigger("selection:comic:add", this.model);
		} else {
			this.$el.find('.checked-comic .glyphicon').addClass('glyphicon-unchecked')
			this.$el.find('.checked-comic .glyphicon').removeClass('glyphicon-check')
			mylar.pubsub.trigger("selection:comic:remove", this.model);
		}
	},
	markComic: function(e){
		mylar.pubsub.trigger("mark:single", $(e.currentTarget).data('action'), this.model);
	}
});

mylar.views.comicCover = Backbone.View.extend({
	tagName: 'div',
	className: 'col-xs-6 col-sm-4 col-md-3 col-lg-2 col-xl-1 cover',
	model: mylar.models.comic,
	template: Handlebars.compile( $('#cover-gallery-single-cover').html() ),
	actions: [],
	events: {
		'click .checked-comic' : 'checkComic',
		'click .mark-comic'	   : 'markComic',
	},
	initialize: function(){
		//this.render()
		mylar.pubsub.on('selection:update', this.maybeRender, this)
	},
	setActions: function(actions){
		this.actions = actions;
	},
	maybeRender: function( models ){
		this.render();
	},
	render: function(){
		var templateData = _.extend(this.model.toJSON(), {
			'selected': mylar.selectedComics.isSelected( this.model ),
			actions: this.actions
		});
		//console.log(templateData);
		this.$el.html( this.template( templateData ) );
		this.$el.find('.panel-title a').css('width', this.$el.find('.panel-body > img').width() )
		return this.$el;
	},
	checkComic: function(){
		if( this.$el.find('.checked-comic .glyphicon').hasClass('glyphicon-unchecked') ){
			this.$el.find('.checked-comic .glyphicon').removeClass('glyphicon-unchecked')
			this.$el.find('.checked-comic .glyphicon').addClass('glyphicon-check')
			mylar.pubsub.trigger("selection:comic:add", this.model);
		} else {
			this.$el.find('.checked-comic .glyphicon').addClass('glyphicon-unchecked')
			this.$el.find('.checked-comic .glyphicon').removeClass('glyphicon-check')
			mylar.pubsub.trigger("selection:comic:remove", this.model);
		}
	},
	markComic: function(e){
		mylar.pubsub.trigger("mark:single", $(e.currentTarget).data('action'), this.model);
	}
});

mylar.views.comicRow = Backbone.View.extend({
	tagName: 'tr',
	model: mylar.models.comic,
	template: Handlebars.compile( $('#comics-table-single-row').html() ),
	actions: [],
	events: {
		'click .checked-comic' : 'checkComic',
		'click .mark-comic'	   : 'markComic',
	},
	initialize: function(){
		//this.render()
		mylar.pubsub.on('selection:update', this.maybeRender, this)
	},
	setActions: function(actions){
		this.actions = actions;
	},
	maybeRender: function( models ){
		this.render();
	},
	render: function(){
		var templateData = _.extend(this.model.toJSON(), {
			'selected': mylar.selectedComics.isSelected( this.model ),
			actions: this.actions
		});
		//console.log(templateData);
		this.$el.html( this.template( templateData ) );
		return this.$el;
	},
	checkComic: function(e){
		if( $(e.target).is(':checked') ){
			mylar.pubsub.trigger("selection:comic:add", this.model);
		} else {
			mylar.pubsub.trigger("selection:comic:remove", this.model);
		}
	},
	markComic: function(e){
		mylar.pubsub.trigger("mark:single", $(e.currentTarget).data('action'), this.model);
	}
})