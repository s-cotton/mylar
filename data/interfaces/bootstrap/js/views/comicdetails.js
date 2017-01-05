var mylar = mylar || {};
var screen = screen || {};

screen.comicdetails = {

	thisScreen: this,

	init: function(){
		console.log('Comic Details Screen JS Loaded');
		mylar.notify.info("Success!");
	},

	docReady: function(){
		mylar.initTable( $('#bsIssuesTable') );

		$('.refreshComic').on('click', screen.comicdetails.refreshComic );
	},

	windowLoad: function(){},
	windowResize: function(){},
	windowUnload: function(){},

	refreshComic: function(){
		mylar.console.log('Comic Refresh Clicked')
	}
}

mylar.registerScreen( screen.comicdetails, [
	'comicdetails'
], {
	ajax: true
});