var mylar = mylar || {};
var screen = screen || {};

screen.config = {

	thisScreen: this,
	deletedNewznabs: 0,
	originalMetaChecked: false,

	init: function(){
		
	},

	docReady: function(){
		
		$('body').on( 'click', '#api_key', screen.config.apiKeyClicked );
		$('body').on( 'click', '#sab_apikey', screen.config.sabKeyClicked );
		$('body').on( 'click', '#generate_api', screen.config.apiKeyGenerate );
		$('body').on( 'click', 'force_rss', screen.config.forceRSS );

		$('body').on( 'click', '#newznab_providers .remove', screen.config.removeNewznabProvider);

		$('body').on( 'click', '#test_32p', screen.config.test32p );
		$('body').on( 'click', '#test_sab', screen.config.testSab );
		$('body').on( 'click', '#find_sabapi', screen.config.findSabAPI );
		$('body').on( 'click', '#nma_test', screen.config.testNMA );
		$('body').on( 'click', '#prowl_test', screen.config.testProwl );
		$('body').on( 'click', '#pushover_test', screen.config.testPushover );
		$('body').on( 'click', '#boxcar_test', screen.config.testBoxcar );
		$('body').on( 'click', '#pushbullet_test', screen.config.testPushbullet );
		$('body').on( 'click', '#telegram_test', screen.config.testTelegram );

		$('body').on( 'click', '#add_newznab', screen.config.addNewznab);
		/**
		 * Setup Hide/Show functionality
		 */
		$('body').on( "change", '#enable_https', screen.config.hideShowHTTPSOptions );
		$('body').on( "change", '#api_enabled', screen.config.hideShowAPIOptions );
		$('body').on( "change", '#enforce_perms', screen.config.hideShowPermissionOptions );
		$('body').on( "change", '[name="nzb_downloader"]', screen.config.hideShowNZBOptions );
		$('body').on( "change", '#enable_torrents', screen.config.hideShowTorrentOptions )
		$('body').on( "change", '[name="torrent_downloader"]', screen.config.hideShowTorrentClientOptions );
		$('body').on( "change", '#local_watchdir', screen.config.hideShowLocalWatchDirOptions );
		$('body').on( "change", '#remote_watchdir', screen.config.hideShowRemoteWatchDirOptions );
		$('body').on( "change", '#rtorrent_ssl', screen.config.hideShowRTorrentSSLOptions );
		$('body').on( "change", '#enable_rss', screen.config.hideShowRSSSearchOptions );
		$('body').on( "change", '#usenzbsu', screen.config.hideShowNZBSUOptions );
		$('body').on( "change", '#usedognzb', screen.config.hideShowDogNZBOptions );
		$('body').on( "change", '#enable_torrent_search', screen.config.hideShowTorrentSearchOptions );
		$('body').on( "change", '#enable_32p', screen.config.hideShow32POptions );
		$('body').on( "change", '[name="mode_32p"]', screen.config.hideShow32PTypeOptions );
		$('body').on( "change", '#enable_torznab', screen.config.hideShowTorznabOptions );
		$('body').on( "change", '#usenewznab', screen.config.hideShowNewzNABOptions );
		$('body').on( "change", '#use_minsize', screen.config.hideShowMinSizeOptions );
		$('body').on( "change", '#use_maxsize', screen.config.hideShowMaxSizeOptions );
		$('body').on( "change", '#enable_ddump', screen.config.hideShowDuplicateDumpOptions );
		$('body').on( "change", '#enable_failed', screen.config.hideShowFailedOptions );
		$('body').on( "change", '#post_processing', screen.config.hideShowPostProcessingOptions );
		$('body').on( "change", '#enable_check_folder', screen.config.hideShowCheckFolderOptions );
		$('body').on( "change", '#enable_pre_scripts', screen.config.hideShowPreScriptOptions );
		$('body').on( "change", '#enable_extra_scripts', screen.config.hideShowPostScriptOptions );
		$('body').on( "change", '#enable_meta', screen.config.hideShowMetaOptions );
		$('body').on( "change", '#cbr2cbz', screen.config.hideShowCBR2CBZOptions );
		$('body').on( "change", '#rename_files', screen.config.hideShowRenameFilesOptions );
		$('body').on( "change", '#replace_spaces', screen.config.hideShowReplaceSpacesOptions );
		$('body').on( "change", '#zero_level', screen.config.hideShowZeroLevelOptions );
		$('body').on( "change", '#prowl_enabled', screen.config.hideShowProwlOptions );
		$('body').on( "change", '#nma_enabled', screen.config.hideShowNMAOptions );
		$('body').on( "change", '#pushover_enabled', screen.config.hideShowPushoverOptions );
		$('body').on( "change", '#boxcar_enabled', screen.config.hideShowBoxcarOptions );
		$('body').on( "change", '#pushbullet_enabled', screen.config.hideShowPushbulletOptions );
		$('body').on( "change", '#telegram_enabled', screen.config.hideShowTelegramOptions );

		$('body').on( 'change', "#file_opts", screen.config.hideShowBadMeta );
		screen.config.originalMetaChecked = $('#enable_meta').is(':checked');

		/**
		 * Initialize Hide/Show functionality
		 */
		for( var methodI in screen.config ){
			if( methodI.indexOf('hideShow') == 0 ){
				screen.config[methodI]();
			}
		}
		
	},

	windowLoad: function(){},
	windowResize: function(){},
	windowUnload: function(){},


	addNewznab: function(){
		mylar.console.log("Adding New Newznab");
		var intId = $("#newznab_providers > div").length + screen.config.deletedNewznabs + 1;
		mylar.console.log( intId );
		var newNewznab = $('.newznab-template > div').clone();
		$(newNewznab).find('label').each(function(){
			$(this).attr('for', $(this).attr('for') + intId );
		});
		$(newNewznab).find('input').each(function(){
			$(this).attr('name', $(this).attr('name') + intId );
			$(this).attr('id', $(this).attr('id') + intId );
		});
		$(newNewznab).find('h4').append(intId);
		$(newNewznab).find('.remove').append(intId);
		console.log(newNewznab);

		$(newNewznab).insertBefore('#add_newznab');
	},

	apiKeyClicked: function(){
		$('#api_key').select();
	},
	sabKeyClicked: function(){
		$('#sab_apikey').select();
	},
	apiKeyGenerate: function(){
		$.get('generateAPI',
            function(data){
                if (data.error != undefined) {
                    mylar.notify.error(data.error);
                } else {
                	$('#api_key').val(data);	
                	mylar.notify.success("Successfully generated new Mylar API Key");
                }
        });
	},
	forceRSS: function(){
		$.get('force_rss',
            function(data){
                if (data.error != undefined) {
                    mylar.notify.error("Could not force RSS Check");
                } else {
                	mylar.notify.success("Successfully forced RSS Check");
                }
        });
	},

	removeNewznabProvider: function(){
		$(this).parent().remove();
        screen.config.deletedNewznabs = screen.config.deletedNewznabs + 1;
	},

	test32p: function(){
		var startMsg = mylar.notify.info("Testing 32p Service...");
		$.get('test_32p',
            function(data){
                if (data.error != undefined) {
                	mylar.notify.error(data.error);
                	startMsg.close();
                } else {
                	$('#status32p').val(data);
                	startMsg.close();	
                }                
        });
	},

	testSab: function(){
		var startMsg = mylar.notify.info("Testing SAB Service...");
		$.get('SABtest',
            function(data){
                if (data.error != undefined) {
                    mylar.notify.error(data.error);
                	startMsg.close();
                } else {
                	$('#sabstatus').val(data);
                	startMsg.close();
                }                
        });
	},
	findSabAPI: function(){
		var startMsg = mylar.notify.info("Looking for SAB API Key...");
		$.get('findsabAPI',
            function(data){
                if (data.error != undefined) {
                    mylar.notify.error(data.error);
                	startMsg.close();
                } else {
                	$('#sab_apikey').val(data);
                	startMsg.close();	
                }
                
        });
	},

	testNMA: function(){
		var startMsg = mylar.notify.info('Testing Notify My Android Connection...');
		$.get("testNMA", function (data) { 
			mylar.notify.success( data );
			startMsg.close();
		});
	},
	testProwl: function(){
		var startMsg = mylar.notify.info('Testing Prowl Connection...');
		$.get("testprowl", function (data) { 
			mylar.notify.success( data );
			startMsg.close();
		});
	},
	testPushover: function(){
		var startMsg = mylar.notify.info('Testing Pushover Connection...');
		$.get("testpushover", function (data) { 
			mylar.notify.success( data );
			startMsg.close();
		});
	},
	testBoxcar: function(){
		var startMsg = mylar.notify.info('Testing Boxcar Connection...');
		$.get("testboxcar", function (data) { 
			mylar.notify.success( data );
			startMsg.close();
		});
	},
	testPushbullet: function(){
		var startMsg = mylar.notify.info('Testing Pushbullet Connection...');
		$.get("testpushbullet", function (data) { 
			mylar.notify.success( data );
			startMsg.close();
		});
	},
	testTelegram: function(){
		var startMsg = mylar.notify.info('Testing Telegram Connection...');
		$.get("testtelegram", function (data) { 
			mylar.notify.success( data );
			startMsg.close();
		});
	},

	hideShowBadMeta: function(){
		mylar.console.log( $('#file_opts').val() );
		if( $('#file_opts').val() == 'hardlink' || $('#file_opts').val() == 'softlink'  ){
			$('.bad_meta').show();
			$('#enable_meta').attr('disabled','disabled');
			$('#enable_meta').removeAttr('checked');
		} else {
			$('.bad_meta').hide();
			$('#enable_meta').removeAttr('disabled');
			if( screen.config.originalMetaChecked ){
				$('#enable_meta').attr('checked','checked');
			}
		}
	},

	hideShowProwlOptions: function(){ 				screen.config.defaultShowIfChecked('prowl_enabled'); },
	hideShowNMAOptions: function(){ 				screen.config.defaultShowIfChecked('nma_enabled'); },
	hideShowPushoverOptions: function(){ 			screen.config.defaultShowIfChecked('pushover_enabled'); },
	hideShowBoxcarOptions: function(){ 				screen.config.defaultShowIfChecked('boxcar_enabled'); },
	hideShowPushbulletOptions: function(){ 			screen.config.defaultShowIfChecked('pushbullet_enabled'); },
	hideShowTelegramOptions: function(){ 			screen.config.defaultShowIfChecked('telegram_enabled'); },
	hideShowZeroLevelOptions: function(){			screen.config.defaultShowIfChecked('zero_level'); },
	hideShowReplaceSpacesOptions: function(){		screen.config.defaultShowIfChecked('replace_spaces');	},
	hideShowRenameFilesOptions: function(){			screen.config.defaultShowIfChecked('rename_files');	},
	hideShowPostScriptOptions: function(){			screen.config.defaultShowIfChecked('enable_extra_scripts');	},
	hideShowPreScriptOptions: function(){			screen.config.defaultShowIfChecked('enable_pre_scripts');	},
	hideShowCheckFolderOptions: function(){			screen.config.defaultShowIfChecked('enable_check_folder');	},
	hideShowPostProcessingOptions: function(){		screen.config.defaultShowIfChecked('post_processing');	},
	hideShowFailedOptions: function(){				screen.config.defaultShowIfChecked('enable_failed');	},
	hideShowDuplicateDumpOptions: function(){		screen.config.defaultShowIfChecked('enable_ddump');	},
	hideShowMaxSizeOptions: function(){				screen.config.defaultShowIfChecked('use_maxsize');	},
	hideShowMinSizeOptions: function(){				screen.config.defaultShowIfChecked('use_minsize');	},
	hideShowNewzNABOptions: function(){				screen.config.defaultShowIfChecked('usenewznab');	},
	hideShowTorznabOptions: function(){				screen.config.defaultShowIfChecked('enable_torznab');	},	
	hideShow32POptions: function(){					screen.config.defaultShowIfChecked('enable_32p');	},
	hideShowTorrentSearchOptions: function(){		screen.config.defaultShowIfChecked('enable_torrent_search');	},
	hideShowDogNZBOptions: function(){				screen.config.defaultShowIfChecked('usedognzb');	},
	hideShowNZBSUOptions: function(){				screen.config.defaultShowIfChecked('usenzbsu');	},
	hideShowRSSSearchOptions: function(){			screen.config.defaultShowIfChecked('enable_rss');	},
	hideShowRTorrentSSLOptions: function(){			screen.config.defaultShowIfChecked('rtorrent_ssl');	},
	hideShowLocalWatchDirOptions: function(){		screen.config.defaultShowIfChecked('local_watchdir');	},
	hideShowRemoteWatchDirOptions: function(){		screen.config.defaultShowIfChecked('remote_watchdir');	},
	hideShowHTTPSOptions: function(){				screen.config.defaultShowIfChecked('enable_https', '.https_options');	},
	hideShowAPIOptions: function(){					screen.config.defaultShowIfChecked('api_enabled', '.api_options');		},
	hideShowPermissionOptions: function(){			screen.config.defaultShowIfChecked('enforce_perms', '.perm_options');	},
	hideShowTorrentOptions: function(){				screen.config.defaultShowIfChecked('enable_torrents', '.torrent_options');	},
	hideShowMetaOptions: function(){				screen.config.defaultShowIfChecked('enable_meta'); 	},	

	hideShowCBR2CBZOptions: function(){				screen.config.defaultHideIfChecked('cbr2cbz');	},

	hideShow32PTypeOptions: function(){
		if( $('[name="mode_32p"]:checked').eq(0).val() == '0' ){
			$('.legacymode_32p_options').show();
			$('.authmode_32p_options').hide();
		} else {
			$('.legacymode_32p_options').hide();
			$('.authmode_32p_options').show();
		}
	},

	hideShowNZBOptions: function(){
		$('#sabnzbd_options,#nzbget_options,#blackhole_options').hide();
		switch( $('[name="nzb_downloader"]:checked').eq(0).val() ){
			case '0': $('#sabnzbd_options').show(); 	break;
			case '1': $('#nzbget_options').show();		break;
			case '2': $('#blackhole_options').show();	break;
		}
	},
	hideShowTorrentClientOptions: function(){
		$('#watchlist_options,#utorrent_options,#rtorrent_options,#transmission_options,#deluge_options').hide();
		switch( $('[name="torrent_downloader"]:checked').eq(0).val() ){
			case '0': $('#watchlist_options').show(); break;
			case '1': $('#utorrent_options').show(); break;
			case '2': $('#rtorrent_options').show(); break;
			case '3': $('#transmission_options').show(); break;
			case '4': $('#deluge_options').show(); break;
		}
	},

	defaultShowIfChecked: function(id){
		
		if( arguments.length > 1 ) options_block = arguments[1];
		else options_block = '.' + id + '_options';

		if( $('#' + id ).length ){
			if( $('#' + id ).is(':checked') ) $( options_block ).show();
			else $( options_block ).hide();	
		}		
	},

	defaultHideIfChecked: function(id){
		
		if( arguments.length > 1 ) options_block = arguments[1];
		else options_block = '.' + id + '_options';

		if( $('#' + id ).length ){
			if( $('#' + id ).is(':checked') ) $( options_block ).hide();
			else $( options_block ).show();
		}
	}

}

mylar.registerScreen( screen.config, [
	'config'
], {
	ajax: true
});