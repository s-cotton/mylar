#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  This file is part of Mylar.
#
#  Mylar is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Mylar is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Mylar.  If not, see <http://www.gnu.org/licenses/>.

import mylar
from mylar import db, mb, importer, search, PostProcessor, versioncheck, logger, helpers
import simplejson as simplejson
import cherrypy
import os
import urllib2
import cache
import imghdr
from operator import itemgetter
from cherrypy.lib.static import serve_file, serve_download

cmd_list = [
    # Reading List Screen
    'readslist','markreads','removefromreadlist','markasRead','syncfiles','removefromreadlist','forcenewcheck','clearfilecache',
    # Comic Details Screen
    'refreshSeries','manualRename','forceRescan','group_metatag','resumeSeries','pauseSeries','addtoreadlist','queueit','unqueueissue','coverComposition',
    # Config
    'generateAPI','force_rss','clearLogs'
    ]


class Ajax(object):

    def __init__(self):
        self.apikey = None
        self.cmd = None
        self.id = None
        self.img = None
        self.file = None
        self.filename = None
        self.kwargs = None
        self.data = None
        self.callback = None
        self.apitype = None

    def checkParams(self, *args, **kwargs):
        #@cherrypy.tools.json_in()
        if 'apikey' not in kwargs:
            self.data = self._error_with_message('Missing api key')
            return

        if 'cmd' not in kwargs:
            self.data = self._error_with_message('Missing parameter: cmd')
            return

        if not mylar.API_ENABLED:
            if kwargs['apikey'] != mylar.DOWNLOAD_APIKEY:
               self.data = self._error_with_message('API not enabled')
               return

        if kwargs['apikey'] != mylar.API_KEY and all([kwargs['apikey'] != mylar.DOWNLOAD_APIKEY, mylar.DOWNLOAD_APIKEY != None]):
            self.data = self._error_with_message('Incorrect API key')
            return
        else:
            if kwargs['apikey'] == mylar.API_KEY:
                self.apitype = 'normal'
            elif kwargs['apikey'] == mylar.DOWNLOAD_APIKEY:
                self.apitype = 'download'
            logger.fdebug('Matched to key. Api set to : ' + self.apitype + ' mode.')
            self.apikey = kwargs.pop('apikey')

        if not([mylar.API_KEY, mylar.DOWNLOAD_APIKEY]):
            self.data = self._error_with_message('API key not generated')
            return

        if self.apitype:
            if self.apitype == 'normal' and len(mylar.API_KEY) != 32:
                self.data = self._error_with_message('API key not generated correctly')
                return
            if self.apitype == 'download' and len(mylar.DOWNLOAD_APIKEY) != 32:
                self.data = self._error_with_message('Download API key not generated correctly')
                return
        else:
            self.data = self._error_with_message('API key not generated correctly')
            return

        if kwargs['cmd'] not in cmd_list:
            self.data = self._error_with_message('Unknown command: %s' % kwargs['cmd'])
            return
        else:
            self.cmd = kwargs.pop('cmd')

        self.kwargs = kwargs
        self.data = 'OK'

    def fetchData(self):

        if self.data == 'OK':
            logger.fdebug('Recieved API command: ' + self.cmd)
            methodToCall = getattr(self, "_" + self.cmd)
            result = methodToCall(**self.kwargs)
            cherrypy.response.headers['Content-Type'] = "application/json"
            return simplejson.dumps(self.data)
        else:
            return self.data

    def _error_with_message(self, message):
        #@cherrypy.tools.json_out()
        error = {'error': {'message': message} }
        cherrypy.response.headers['Content-Type'] = "application/json"
        cherrypy.response.status = 500
        cherrypy.response.body = simplejson.dumps(error)
        return error

    def _success_with_message(self, **message):
        #@cherrypy.tools.json_out()
        success = {'success': {'message': message} }
        cherrypy.response.headers['Content-Type'] = "application/json"
        cherrypy.response.status = 200
        cherrypy.response.body = simplejson.dumps(success)
        return success

    #
    # Reading List AJAX Actions
    #

    def _markreads(self, **kwargs):
        # TODO
        self.data = self._success_with_message(**kwargs)
        return;

    def _removefromreadlist(self, **kwargs):
        # TODO
        self.data = self._success_with_message(**kwargs)
        return;

    def _markasRead(self, **kwargs):
        # TODO
        self.data = self._success_with_message(**kwargs)
        return;

    def _syncfiles(self, **kwargs):
        # TODO
        self.data = self._success_with_message(**kwargs)
        return;

    def _removefromreadlist(self, **kwargs):
        # TODO
        self.data = self._success_with_message(**kwargs)
        return;

    def _forcenewcheck(self, **kwargs):
        # TODO
        self.data = self._success_with_message(**kwargs)
        return;

    def _clearfilecache(self, **kwargs):
        # TODO
        self.data = self._success_with_message(**kwargs)
        return;

    def _refreshSeries(self, **kwargs):
        # TODO
        self.data = self._success_with_message(**kwargs)
        return;

    def _manualRename(self, **kwargs):
        # TODO
        self.data = self._success_with_message(**kwargs)
        return;

    def _forceRescan(self, **kwargs):
        # TODO
        self.data = self._success_with_message(**kwargs)
        return;

    def _group_metatag(self, **kwargs):
        # TODO
        self.data = self._success_with_message(**kwargs)
        return;

    def _resumeSeries(self, **kwargs):
        # TODO
        self.data = self._success_with_message(**kwargs)
        return;

    def _pauseSeries(self, **kwargs):
        # TODO
        self.data = self._success_with_message(**kwargs)
        return;

    def _addtoreadlist(self, **kwargs):
        # TODO
        self.data = self._success_with_message(**kwargs)
        return;

    def _queueit(self, **kwargs):
        # TODO
        self.data = self._success_with_message(**kwargs)
        return;

    def _unqueueissue(self, **kwargs):
        # TODO
        self.data = self._success_with_message(**kwargs)
        return;
    
    def _generateAPI(self, **kwargs):
        import hashlib, random

        apikey = hashlib.sha224(str(random.getrandbits(256))).hexdigest()[0:32]
        logger.info("New API generated")
        mylar.API_KEY = apikey

        self.data = self._success_with_message(apikey);
        return;

    def _force_rss(self, **kwargs):
        # TODO
        self.data = self._success_with_message(**kwargs)
        return;

    def _clearLogs(self, **kwargs):
        # TODO
        self.data = self._success_with_message(**kwargs)
        return;

    def _coverComposition(self, **kwargs):
        if kwargs['issueID'] is not None:
            status = helpers.IssueCovers(kwargs['comicID'],kwargs['issueID'])
        else:
            status = helpers.IssueCovers(kwargs['comicID'])

        if status:
            self.data = self._success_with_message(**kwargs)
        else:
            self.data = self._error_with_message(**kwargs)
        return;


    