var mylar = mylar || {};
var screen = screen || {};

mylar.views.readinglist = Backbone.View.extend({
	el: '.readinglist',
	collection: null,
	gridBrowser: null,
	coverBrowser: null,
	tableBrowser: null,
	pager: null,
	selected: null,

	context: "issues",
	actions: [
		/*{ 
			key   : 'delete',  
			label : 'Delete Series',  
			icon  : 'trash'    
		},*/
	],
	selectables: [
		/*{ 
			key    : 'ended',   
			label  : 'Ended',   
			icon   : 'time',         
			target : 'Ended'   
		},*/
	],

	views: [
		{ 
			key     : 'grid',    
			label   : 'Grid', 	
			icon    : 'th-large', 
			default : true  
		},
		{ 
			key     : 'list', 	  
			label   : 'List', 	
			icon    : 'list',     
			default : false 
		},
		{ 
			key     : 'covers',  
			label   : 'Covers', 	
			icon    : 'film',     
			default : false 
		}
	],

	sortables: [
		/*{ 
			key     : 'name',   
			label   : 'Name',   
			target  : 'ComicSortName', 
			default : true  
		},*/
	],
	searchables: [
		{ key: 'name', label: 'Name', target: 'ComicName', altName: [ 'ComicName', 'ComicSortName', 'Title' ] },
		{ key: 'year', label: 'Year', target: 'ComicYear', altName: [ 'ComicYear', 'Started' ] },
	],

	initialize: function(){
		this.collection = mylar.issues;
		
		this.pager = new mylar.views.mylarPagerAndFilter();
		this.pager.setContext( this.context );
		this.pager.setActions( this.actions );
		this.pager.setSelectable( this.selectables );
		this.pager.setViews( this.views );
		this.pager.setSortable( this.sortables );
		this.pager.setSearchable( this.searchables );
		this.pager.render();

		this.tableBrowser = new mylar.views.issueTableBrowser({actions: this.actions});
		this.tableBrowser.setActions( this.actions );
		this.tableBrowser.render();

		this.gridBrowser = new mylar.views.issueGridBrowser({actions: this.actions});
		this.gridBrowser.setActions( this.actions );
		this.gridBrowser.render();
		
		this.coverBrowser = new mylar.views.issueCoverBrowser({actions: this.actions});
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
		var startMsg = mylar.notify.info( 'Initiating refresh of ' + ids.length + ' Comics' );
		mylar.ajax({
			cmd: 'refreshSeries',
			IssueID: ids
		}).fail(function(){
			mylar.notify.error( 'Could not refresh Comics' );
			startMsg.close();
		}).done(function(){
			mylar.notify.success( ids.length + ' Comics are being refreshed.' );
			startMsg.close();
		});
		if( screen.comicdetails.debug ){
			//doAjaxCall('refreshSeries?ComicID=' + screen.comicdetails.comicID, $(this), 'table' );	
		}	
	},

	markResume:  function( ids ) {
		console.log('Marking: Resume',ids);
	},

	changeSelected: function( dataObj ){
		mylar.selectedComics.clearSelected(false);
		if( dataObj.selected.length == 1 && dataObj.selected[0] == 'all' ){
			console.log('attempting all', this.tableBrowser.collection.fullCollection.length );
			var relevantComics = this.tableBrowser.fullCollection;
			mylar.selectedComics.add(relevantComics,{silent:true});
		} else {
			for( var i in dataObj.selected ){
				var relevantSelectable = _.find(this.selectables,function(selectable){ return selectable.key == dataObj.selected[i]; });
				console.log(relevantSelectable);
				var filterObj = { Status: relevantSelectable.target };
				var relevantComics = this.tableBrowser.collection.fullCollection.filter(filterObj);
				mylar.selectedComics.add(relevantComics,{silent:true});
			}	
		}		
		mylar.selectedComics.broadcastSelection();
	}
	
});

$(document).ready(function(){
	screen.readinglist = new mylar.views.readinglist();
});
