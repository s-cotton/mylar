var mylar = mylar || {};

mylar.views = mylar.views || {};

mylar.views.comicCoverBrowser = Backbone.View.extend({
	el: '.cover-browser',
	template: Handlebars.compile( $('#cover-gallery-container').html() ),
	collection: null,
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
	},

	setCollection: function(){
		if( this.searchValue.length ){
			this.collection = new mylar.pageableCollections.Comics( mylar.comics.filterValues( this.searchValue ),{
				mode: "client",
				comparator: function (model) { return model.get("ComicID"); },
			});
		} else {
			this.collection = new mylar.pageableCollections.Comics( initialData.comics,{
				mode: "client",
				comparator: function (model) { return model.get("ComicID"); },
			});
		}
	},

	render: function(){
		var that = this;

		var templateData = this.dataObj();
		console.log( templateData );
		this.$el.html( this.template( templateData ) );

		this.renderCovers();

		this.setupPagination();
		
		return this;
	},

	renderCovers: function(){
		this.$el.find('.covers').empty();
		
		this.collection.setPageSize( this.perPage );
		if( this.currentPage > this.collection.state.totalPages ) this.currentPage = this.collection.state.totalPages;

		this.collection.getPage( this.currentPage );

		for( var single_model in this.collection.models ){
			var thisCover = new mylar.views.comicCover({ model: this.collection.models[ single_model ] });
			this.$el.find('.covers').append( thisCover.render() );
		}
		this.setClearfix();
		
	},

	setupPagination: function(){
		var that = this;
		this.$el.find('.pagination').twbsPagination("destroy");
		if( this.collection.state.totalPages > 0 ){
			this.$el.find('.pagination').twbsPagination({
		        totalPages: this.collection.state.totalPages,
		        visiblePages: 7,
		        startPage: this.currentPage,
		        onPageClick: function(event,page){
		        	if( that.currentPage != page ){
		        		that.changePage(page);	
		        	}
		        }
		    });	
		}		
	},

	dataObj: function(){
		return {
			perpage: this.getPerPage()
		}
	},

	getPerPage: function(){
		var sizes = [];
		if( mylar.viewport.is('lg') || mylar.viewport.is('md') ){
			sizes = [
				{ count: 8 },
				{ count: 16, default: true },
				{ count: 32 },
				{ count: 64 }
			];
		} else if ( mylar.viewport.is('sm') || mylar.viewport.is('xs') ){
			sizes = [
				{ count: 10 },
				{ count: 20, default: true },
				{ count: 40 },
				{ count: 80 }
			];
		}
		return sizes;
	},

	changePage: function(page){
		this.currentPage = page;
		/*console.log(event,page);*/
		console.log('Changed Page?',page);
		this.renderCovers();
	},

	changePageSize: function(e){
		$(e.target).parents('ul').eq(0).find('.active').removeClass('active');
		$(e.target).addClass('active');
		this.perPage = $(e.target).data('perpage');
		this.renderCovers();
		this.setupPagination();
	},

	changeSortBy: function(e){
		$(e.target).parents('ul').eq(0).find('.active').removeClass('active');
		$(e.target).addClass('active');
		var sortBy = $(e.target).data('sortby');
		//console.log('new',sortBy,'old',this.sortBy,'dir',this.sortDir);
		if( sortBy != this.sortBy ){
			this.sortBy = sortBy;
			this.sortDir = 1;
			this.collection.setSorting( this.sortBy, 1, {full: true} );
		} else {
			this.sortDir = (this.sortDir == 1) ? -1 : 1;
			this.collection.setSorting( this.sortBy, this.sortDir, {full: true} );
		}		
		this.collection.fullCollection.sort();
		this.renderCovers();
	},

	filterComics: function(){
		if( this.searchValue.length == 0 ) this.currentPage = 1;
		this.searchValue = this.$el.find('[name="search"]').val();
		console.log(this.searchValue);
		this.setCollection();
		this.renderCovers();
		this.setupPagination();
	},

	resetSearch: function(){
		this.$el.find('[name="search"]').val('');
		this.searchValue = '';
		this.sortBy = "ComicSortName";
		this.sortDir = 1;
		this.currentPage = 1;
		this.perPage = 16;
		this.setCollection();
		this.renderCovers();
		this.setupPagination();
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