var mylar = mylar || {};
var screen = screen || {};

mylar.views.managecomics = Backbone.View.extend({
	el: '.managecomics',
	collection: null,
	gridBrowser: null,
	coverBrowser: null,
	tableBrowser: null,
	pager: null,
	selected: null,

	context: "comics",
	actions: [
		{ key: 'delete',  label: 'Delete Series',  icon: 'trash'    },
		{ key: 'metatag', label: 'MetaTag Series', icon: 'tags'     },
		{ key: 'pause',   label: 'Pause Series',   icon: 'pause'    },
		{ key: 'recheck', label: 'Recheck Files',  icon: 'eye-open' },
		{ key: 'refresh', label: 'Refresh Series', icon: 'refresh'  },
		{ key: 'resume',  label: 'Resume Series',  icon: 'play'     },
	],
	selectables: [
		{ key: 'ended',   label: 'Ended',   icon: 'time',         target: 'Ended'   },
		{ key: 'loading', label: 'Loading', icon: 'refresh',      target: 'Loading' },
		{ key: 'error',   label: 'Error',   icon: 'warning-sign', target: 'Error'   },
		{ key: 'active',  label: 'Active',  icon: 'thumbs-up',    target: 'Active'  },
	],

	views: [
		{ key: 'grid',    label: 'Grid', 	icon: 'th-large', default: true  },
		{ key: 'list', 	  label: 'List', 	icon: 'list',     default: false },
		{ key: 'covers',  label: 'Covers', 	icon: 'film',     default: false }
	],

	sortables: [
		{ key: 'name',   label: 'Name',   target: 'ComicSortName', default: true  },
		{ key: 'year',   label: 'Year',   target: 'ComicYear',     default: false },
		{ key: 'status', label: 'Status', target: 'Status',        default: false },
		{ key: 'issues', label: 'Issues', target: 'haveissues',    default: false },
		{ key: 'latest', label: 'Latest', target: 'LatestDate',    default: false },
	],

	initialize: function(){
		this.collection = mylar.comics;
		
		this.pager = new mylar.views.comicPagerAndFilter();
		this.pager.setContext("comics");
		this.pager.setActions( this.actions );
		this.pager.setSelectable( this.selectables );
		this.pager.setViews( this.views );
		this.pager.setSortable( this.sortables );
		this.pager.render();

		this.tableBrowser = new mylar.views.comicTableBrowser({actions: this.actions});
		this.tableBrowser.setActions( this.actions );
		this.tableBrowser.render();

		this.gridBrowser = new mylar.views.comicGridBrowser({actions: this.actions});
		this.gridBrowser.setActions( this.actions );
		this.gridBrowser.render();
		
		this.coverBrowser = new mylar.views.comicCoverBrowser({actions: this.actions});
		this.coverBrowser.setActions( this.actions );
		this.coverBrowser.render();
		

		this.pager.setInitialLayout();

		mylar.pubsub.on( "mark:selected", this.markSelected, this );
		mylar.pubsub.on( "mark:single", this.markSingle, this );
		mylar.pubsub.on( "pager:changeSelected", this.changeSelected, this );

	},

	markSelected: function( action ){
		switch( action ){
			case 'delete':  
				this.markDelete( mylar.selectedComics.pluck("ComicID") );  
				break;
			case 'metatag': 
				this.markMetatag( mylar.selectedComics.pluck("ComicID") ); 
				break;
			case 'pause':   
				this.markPause( mylar.selectedComics.pluck("ComicID") );   
				break;
			case 'recheck': 
				this.markRecheck( mylar.selectedComics.pluck("ComicID") ); 
				break;
			case 'refresh': 
				this.markRefresh( mylar.selectedComics.pluck("ComicID") ); 
				break;
			case 'resume':  
				this.markResume([ model.attributes.ComicID ]);  
				break;
		}
	},

	markSingle: function( action, model ){
		switch( action ){
			case 'delete':  
				this.markDelete([ model.attributes.ComicID ]);  
				break;
			case 'metatag': 
				this.markMetatag([ model.attributes.ComicID ]); 
				break;
			case 'pause':   
				this.markPause([ model.attributes.ComicID ]);   
				break;
			case 'recheck': 
				this.markRecheck([ model.attributes.ComicID ]); 
				break;
			case 'refresh': 
				this.markRefresh([ model.attributes.ComicID ]); 
				break;
			case 'resume':  
				this.markResume([ model.attributes.ComicID ]);  
				break;
		}
	},

	markDelete:  function( ids ) {
		console.log('Marking: Delete',ids);
	},

	markMetatag: function( ids ) {
		console.log('Marking: Metatag',ids);
	},

	markPause:   function( ids ) {
		console.log('Marking: Pause',ids);
	},

	markRecheck: function( ids ) {
		console.log('Marking: Recheck',ids);
	},

	markRefresh: function( ids ) {
		console.log('Marking: Refresh',ids);
	},

	markResume:  function( ids ) {
		console.log('Marking: Resume',ids);
	},

	changeSelected: function( dataObj ){
		mylar.selectedComics.clearSelected(false);
		for( var i in dataObj.selected ){
			var filterObj = { Status: dataObj.selected[i] };
			var relevantComics = this.collection.filter(filterObj);
			mylar.selectedComics.add(relevantComics,{silent:true});
		}
		mylar.selectedComics.broadcastSelection();
	}
	
});

$(document).ready(function(){
	screen.managecomics = new mylar.views.managecomics();
});
