var mylar = mylar || {};
var screen = screen || {};

screen.comicdetails = {

	thisScreen: this,

	init: function(){
		console.log('Comic Details Screen JS Loaded');
	},

	docReady: function(){
		mylar.initTable( $('#bsIssuesTable') );
	},

	windowLoad: function(){},
	windowResize: function(){},
	windowUnload: function(){},
}

mylar.registerScreen( screen.comicdetails, [
	'comicdetails'
], {
	ajax: true
});