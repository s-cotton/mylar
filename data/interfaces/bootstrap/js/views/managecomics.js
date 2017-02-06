var mylar = mylar || {};
var screen = screen || {};

mylar.views.managecomics = Backbone.View.extend({
	el: '.managecomics',
	coverBrowser: null,
	tableBrowser: null,
	pager: null,

	initialize: function(){
		this.pager = new mylar.views.comicPagerAndFilter();
		this.pager.setContext("comics");
		this.pager.setActions([
				{ key: 'delete',  label: 'Delete Series',  icon: 'trash'    },
				{ key: 'metatag', label: 'MetaTag Series', icon: 'tags'     },
				{ key: 'pause',   label: 'Pause Series',   icon: 'pause'    },
				{ key: 'recheck', label: 'Recheck Files',  icon: 'eye-open' },
				{ key: 'refresh', label: 'Refresh Series', icon: 'refresh'  },
				{ key: 'resume',  label: 'Resume Series',  icon: 'play'     },
		]);
		this.pager.setSelectable([
			{ key: 'ended',   label: 'Ended',   icon: 'time'         },
			{ key: 'loading', label: 'Loading', icon: 'refresh'      },
			{ key: 'error',   label: 'Error',   icon: 'warning-sign' },
			{ key: 'active',  label: 'Active',  icon: 'thumbs-up'    },
		]);
		this.pager.setViews([
			{ key: 'grid',    label: 'Grid', icon: 'th-large', default: true },
			{ key: 'list', 	  label: 'List', icon: 'list', default: false }
		]);
		this.pager.render();
		this.tableBrowser = new mylar.views.comicTableBrowser();
		this.coverBrowser = new mylar.views.comicCoverBrowser();
		this.pager.setInitialLayout();

	}
});

var thisPage = new mylar.views.managecomics();