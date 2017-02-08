var mylar = mylar || {};
var screen = screen || {};

mylar.views.managecomics = Backbone.View.extend({
	el: '.managecomics',
	collection: null,
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

		this.tableBrowser = new mylar.views.comicTableBrowser();
		this.coverBrowser = new mylar.views.comicGridBrowser();
		this.coverBrowser = new mylar.views.comicCoverBrowser();

		this.pager.setInitialLayout();

		mylar.pubsub.on( "pager:markSelected", this.markSelected, this );
		mylar.pubsub.on( "pager:changeSelected", this.changeSelected, this );

	},

	markSelected: function( dataObj ){
		console.log(dataObj);
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
