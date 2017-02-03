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

	currentPage: 1,
	
	events: {
		"click .change-page-size"	: "changePageSize",
		"click .change-sort-by"		: "changeSortBy"
	},
	initialize: function(){
		this.collection = new mylar.pageableCollections.Comics( initialData.comics,{
			mode: "client",
			comparator: function (model) { return model.get("ComicID"); },
		});

		this.render();
	},
	render: function(){
		var that = this;

		this.collection.setPageSize( this.perPage );
		if( this.currentPage > this.collection.state.totalPages ) this.currentPage = this.collection.state.totalPages;

		this.collection.getPage( this.currentPage );
		var templateData = this.dataObj();
		console.log( templateData );
		this.$el.html( this.template( templateData ) );
		for( var single_model in this.collection.models ){
			var thisCover = new mylar.views.comicCover({ model: this.collection.models[ single_model ] });
			this.$el.find('.covers').append( thisCover.render() );
		}
		this.setClearfix();
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
		return this;
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
				{ count: 16 },
				{ count: 32 },
				{ count: 64 }
			];
		} else if ( mylar.viewport.is('sm') || mylar.viewport.is('xs') ){
			sizes = [
				{ count: 10 },
				{ count: 20 },
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
		this.render();
	},
	changePageSize: function(e){
		this.perPage = $(e.target).data('perpage');
		this.render();
	},
	changeSortBy: function(e){
		var sortBy = $(e.target).data('sortby');
		console.log('new',sortBy,'old',this.sortBy,'dir',this.sortDir);
		if( sortBy != this.sortBy ){
			this.sortBy = sortBy;
			this.sortDir = 1;
			this.collection.setSorting( this.sortBy, 1, {full: true} );
		} else {
			this.sortDir = (this.sortDir == 1) ? -1 : 1;
			this.collection.setSorting( this.sortBy, this.sortDir, {full: true} );
		}		
		this.collection.fullCollection.sort();
		this.render();
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