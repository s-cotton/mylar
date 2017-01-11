var mylar = mylar || {};
var screen = screen || {};

screen.config = {

	thisScreen: this,

	init: function(){
		
	},

	docReady: function(){
		
		$('body').on( 'click', '#api_key', screen.config.apiKeyClicked );
		$('body').on( 'click', '#generate_api', screen.config.apiKeyGenerate );
		$('body').on( 'click', 'force_rss', screen.config.forceRSS );


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
		
		
		
		
		

		/**
		 * Initialize Hide/Show functionality
		 */
		screen.config.hideShowHTTPSOptions();
		screen.config.hideShowAPIOptions();
		screen.config.hideShowPermissionOptions();
		screen.config.hideShowTorrentOptions();
		screen.config.hideShowNZBOptions();
		screen.config.hideShowTorrentClientOptions();
		screen.config.hideShowLocalWatchDirOptions();
		screen.config.hideShowRemoteWatchDirOptions();
		screen.config.hideShowRTorrentSSLOptions();
		screen.config.hideShowRSSSearchOptions();
		screen.config.hideShowNZBSUOptions();
		screen.config.hideShowDogNZBOptions();
		screen.config.hideShowTorrentSearchOptions();
		screen.config.hideShow32POptions();
		screen.config.hideShow32PTypeOptions();
		screen.config.hideShowTorznabOptions();
		screen.config.hideShowNewzNABOptions();
		screen.config.hideShowMinSizeOptions();
		screen.config.hideShowMaxSizeOptions();
		screen.config.hideShowDuplicateDumpOptions();
		screen.config.hideShowFailedOptions();
		screen.config.hideShowPostProcessingOptions();
		screen.config.hideShowCheckFolderOptions();
		screen.config.hideShowPreScriptOptions();
		screen.config.hideShowPostScriptOptions();
		screen.config.hideShowMetaOptions();
		screen.config.hideShowCBR2CBZOptions();
		screen.config.hideShowRenameFilesOptions();
		
	},

	windowLoad: function(){},
	windowResize: function(){},
	windowUnload: function(){},

	apiKeyClicked: function(){
		$('#api_key').select()
	},
	apiKeyGenerate: function(){
		mylar.ajax({
			cmd: "generateAPI"
		}).fail(function(){
			mylar.notify.error("Could not generate a new Mylar API Key");
		}).done(function(data){
			mylar.console.log(data);
			mylar.notify.success("Successfully generated new Mylar API Key");
		});
		/*$.get('generateAPI',
            function(data){
                if (data.error != undefined) {
                    alert(data.error);
                    return;
                }
                $('#api_key').val(data);
        });*/
	},
	forceRSS: function(){
		mylar.ajax({
			cmd: "force_rss"
		}).fail(function(){
			mylar.notify.error("Could not force RSS Check");
		}).done(function(data){
			mylar.notify.success("Successfully forced RSS Check");
		});
	},

	hideShowRenameFilesOptions: function(){
		if( $('#rename_files').is(':checked') ) $('.rename_files_options').show();
		else $('.rename_files_options').hide();
	},
	hideShowMetaOptions: function(){
		if( $('#enable_meta').is(':checked') ) $('.enable_meta_options').show();
		else $('.enable_meta_options').hide();
	},
	hideShowCBR2CBZOptions: function(){
		// NOTE THAT THIS ONE IS BACKWARDS, BUT WHATEVER, PATTERNS LIVE FOREVER
		if( $('#cbr2cbz').is(':checked') ) $('.cbr2cbz_options').hide();
		else $('.cbr2cbz_options').show();
	},
	hideShowPostScriptOptions: function(){
		if( $('#enable_extra_scripts').is(':checked') ) $('.enable_extra_scripts_options').show();
		else $('.enable_extra_scripts_options').hide();
	},
	hideShowPreScriptOptions: function(){
		if( $('#enable_pre_scripts').is(':checked') ) $('.enable_pre_scripts_options').show();
		else $('.enable_pre_scripts_options').hide();
	},
	hideShowCheckFolderOptions: function(){
		if( $('#enable_check_folder').is(':checked') ) $('.enable_check_folder_options').show();
		else $('.enable_check_folder_options').hide();
	},
	hideShowPostProcessingOptions: function(){
		if( $('#post_processing').is(':checked') ) $('.post_processing_options').show();
		else $('.post_processing_options').hide();
	},
	hideShowFailedOptions: function(){
		if( $('#enable_failed').is(':checked') ) $('.enable_failed_options').show();
		else $('.enable_failed_options').hide();
	},
	hideShowDuplicateDumpOptions: function(){
		if( $('#enable_ddump').is(':checked') ) $('.enable_ddump_options').show();
		else $('.enable_ddump_options').hide();
	},
	hideShowMaxSizeOptions: function(){
		if( $('#use_maxsize').is(':checked') ) $('.use_maxsize_options').show();
		else $('.use_maxsize_options').hide();
	},
	hideShowMinSizeOptions: function(){
		if( $('#use_minsize').is(':checked') ) $('.use_minsize_options').show();
		else $('.use_minsize_options').hide();
	},
	hideShowNewzNABOptions: function(){
		if( $('#usenewznab').is(':checked') ) $('.usenewznab_options').show();
		else $('.usenewznab_options').hide();
	},
	hideShowTorznabOptions: function(){
		if( $('#enable_torznab').is(':checked') ) $('.enable_torznab_options').show();
		else $('.enable_torznab_options').hide();
	},
	hideShow32PTypeOptions: function(){
		if( $('[name="mode_32p"]:checked').eq(0).val() == '0' ){
			$('.legacymode_32p_options').show();
			$('.authmode_32p_options').hide();
		} else {
			$('.legacymode_32p_options').hide();
			$('.authmode_32p_options').show();
		}
	},
	hideShow32POptions: function(){
		if( $('#enable_32p').is(':checked') ) $('.enable_32p_options').show();
		else $('.enable_32p_options').hide();
	},
	hideShowTorrentSearchOptions: function(){
		if( $('#enable_torrent_search').is(':checked') ) $('.enable_torrent_search_options').show();
		else $('.enable_torrent_search_options').hide();
	},
	hideShowDogNZBOptions: function(){
		if( $('#usedognzb').is(':checked') ) $('.usedognzb_options').show();
		else $('.usedognzb_options').hide();
	},
	hideShowNZBSUOptions: function(){
		if( $('#usenzbsu').is(':checked') ) $('.usenzbsu_options').show();
		else $('.usenzbsu_options').hide();
	},
	hideShowRSSSearchOptions: function(){
		if( $('#enable_rss').is(':checked') ) $('.enable_rss_options').show();
		else $('.enable_rss_options').hide();
	},
	hideShowRTorrentSSLOptions: function(){
		if( $('#rtorrent_ssl').is(':checked') ) $('.rtorrent_ssl_options').show();
		else $('.rtorrent_ssl_options').hide();
	},
	hideShowLocalWatchDirOptions: function(){
		if( $('#local_watchdir').is(':checked') ) $('.local_watchdir_options').show();
		else $('.local_watchdir_options').hide();
	},
	hideShowRemoteWatchDirOptions: function(){
		if( $('#remote_watchdir').is(':checked') ) $('.remote_watchdir_options').show();
		else $('.remote_watchdir_options').hide();
	},
	hideShowHTTPSOptions: function(){
		if( $('#enable_https').is(':checked') ) $('.https_options').show();
		else $('.https_options').hide();
	},
	hideShowAPIOptions: function(){
		if( $('#api_enabled').is(':checked') ) $('.api_options').show();
		else $('.api_options').hide();
	},
	hideShowPermissionOptions: function(){
		if( $('#enforce_perms').is(':checked') ) $('.perm_options').show();
		else $('.perm_options').hide();
	},
	hideShowTorrentOptions: function(){
		if( $('#enable_torrents').is(':checked') ) $('.torrent_options').show();
		else $('.torrent_options').hide();
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
	}

}

mylar.registerScreen( screen.config, [
	'config'
], {
	ajax: true
});