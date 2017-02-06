var mylar = mylar || {};
var screen = screen || {};

screen.managecomics = {

	thisScreen: this,
	coverBrowser: null,
	pager: null,

	init: function(){
		
	},

	docReady: function(){

		screen.managecomics.pager = new mylar.views.comicPagerAndFilter();
		screen.managecomics.pager.setContext("comics");
		screen.managecomics.pager.setActions([
				{ key: 'delete',  label: 'Delete Series',  icon: 'trash'    },
				{ key: 'metatag', label: 'MetaTag Series', icon: 'tags'     },
				{ key: 'pause',   label: 'Pause Series',   icon: 'pause'    },
				{ key: 'recheck', label: 'Recheck Files',  icon: 'eye-open' },
				{ key: 'refresh', label: 'Refresh Series', icon: 'refresh'  },
				{ key: 'resume',  label: 'Resume Series',  icon: 'play'     },
		]);
		screen.managecomics.pager.setSelectable([
			{ key: 'ended',   label: 'Ended',   icon: 'time'         },
			{ key: 'loading', label: 'Loading', icon: 'refresh'      },
			{ key: 'error',   label: 'Error',   icon: 'warning-sign' },
			{ key: 'active',  label: 'Active',  icon: 'thumbs-up'    },
		]);
		screen.managecomics.pager.setViews([
			{ key: 'grid',    label: 'Grid', icon: 'th-large', default: true },
			{ key: 'list', 	  label: 'List', icon: 'list', default: false }
		]);
		screen.managecomics.pager.render();
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