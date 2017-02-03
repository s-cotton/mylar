var mylar = mylar || {};

mylar.views = mylar.views || {};

mylar.views.comicCoverBrowser = Backbone.View.extend({
	el: '.cover-browser',
	template: Handlebars.compile( $('#cover-gallery-container').html() ),
	collection: null,
	covers: [],
	perPage: 16,
	currentPage: 1,
	events: {
		//"changePage .pagination-sm"	: "changePage"
	},
	initialize: function(){
		this.collection = new mylar.pageableCollections.Comics( initialData.comics,{
			mode: "client",
			comparator: function (model) { return model.get("ComicID"); },
		});
		this.collection.setPageSize( this.perPage );
		console.log( this.collection.getPage( this.currentPage ) );

		for( var single_model in this.collection.models ){

			console.log(this.collection.models[single_model]);
		}

		this.render();
	},
	render: function(){
		var that = this;
		this.collection.getPage( this.currentPage );
		this.$el.html( this.template() );
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

	changePage: function(page){
		this.currentPage = page;
		/*console.log(event,page);*/
		console.log('Changed Page?',page);
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
	initialize: function(){
		//this.render()
	},
	render: function(){
		this.$el.html( this.template( this.model.toJSON() ) );
		return this.$el;
	}
})