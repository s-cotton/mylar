var mylar = mylar || {};
var screen = screen || {};

screen.managecomics = {

	thisScreen: this,
	collection: null,
	coverBrowser: null,

	init: function(){
		
	},

	docReady: function(){

/*		screen.managecomics.collection = new mylar.pageableCollections.Comics( initialData.comics,{
			mode: "client",
			comparator: function (model) { return model.get("ComicID"); }
		});*/

		screen.managecomics.coverBrowser = new mylar.views.comicCoverBrowser();



		//screen.managecomics.coverBrowser.render();
		/**
		 * Set up click handlers for various actions around page
		 */
		//$('body').on( "click", ".sync-to-device", screen.readlist.syncFiles );
		
	},

	windowLoad: function(){},
	windowResize: function(){},
	windowUnload: function(){},

	
}

mylar.registerScreen( screen.managecomics, [
	'managecomics'
], {
	ajax: true
});