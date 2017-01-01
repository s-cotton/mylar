#  This file is part of Mylar.
# -*- coding: utf-8 -*-
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

from __future__ import with_statement

import os
import sys
import cherrypy
import datetime
from datetime import timedelta, date
import re
import json

from mako.template import Template
from mako.lookup import TemplateLookup
from mako import exceptions

import time
import threading
import csv
import platform
import urllib
import shutil

import mylar

from mylar import logger, db, importer, mb, search, filechecker, helpers, updater, parseit, weeklypull, PostProcessor, librarysync, moveit, Failed, readinglist, notifiers #,rsscheck

import simplejson as simplejson

from operator import itemgetter

def serve_template(templatename, **kwargs):
    interface_dir = os.path.join(str(mylar.PROG_DIR), 'data/interfaces/')
    template_dir = os.path.join(str(interface_dir), mylar.INTERFACE)
    _hplookup = TemplateLookup(directories=[template_dir])
    try:
        template = _hplookup.get_template(templatename)
        return template.render(**kwargs)
    except:
        return exceptions.html_error_template().render()

class WebInterface(object):

#    def filter_request():
#        request = cherrypy.request

#        if mylar.HTTPS_FORCE_ON:
#            request.base = request.base.replace('http://', 'https://')

#    cherrypy.tools.filter_request = cherrypy.Tool('before_request_body', filter_request)

#    _cp_config = { 'tools.filter_reqeust_on': True }

    def index(self):
        if mylar.SAFESTART:
            raise cherrypy.HTTPRedirect("manageComics")
        else:
            raise cherrypy.HTTPRedirect("home")
    index.exposed=True

    def home(self):
        comics = helpers.havetotals()
        return serve_template(templatename="index.html", title="Home", comics=comics)
    home.exposed = True

    def comicDetails(self, ComicID):
        myDB = db.DBConnection()
        comic = myDB.selectone('SELECT * FROM comics WHERE ComicID=?', [ComicID]).fetchone()
        if comic is None:
            if mylar.SAFESTART:
                raise cherrypy.HTTPRedirect("manageComics")
            else:
                raise cherrypy.HTTPRedirect("home")
        #let's cheat. :)
        #comicskip = myDB.select('SELECT * from comics order by ComicSortName COLLATE NOCASE')
        skipno = len(mylar.COMICSORT['SortOrder'])
        lastno = mylar.COMICSORT['LastOrderNo']
        lastid = mylar.COMICSORT['LastOrderID']
        series = {}

        if skipno == 0:
            #it's a blank db, let's just null the values and go.
            series['Current'] = None
            series['Previous'] = None
            series['Next'] = None
        i = 0
        while (i < skipno):
            cskip = mylar.COMICSORT['SortOrder'][i]
            if cskip['ComicID'] == ComicID:
                cursortnum = cskip['ComicOrder']
                series['Current'] = cskip['ComicID']
                if cursortnum == 0:
                    # if first record, set the Previous record to the LAST record.
                    previous = lastid
                else:
                    previous = mylar.COMICSORT['SortOrder'][i -1]['ComicID']

                # if last record, set the Next record to the FIRST record.
                if cursortnum == lastno:
                    next = mylar.COMICSORT['SortOrder'][0]['ComicID']
                else:
                    next = mylar.COMICSORT['SortOrder'][i +1]['ComicID']
                series['Previous'] = previous
                series['Next'] = next
                break
            i+=1

        issues = myDB.select('SELECT * FROM issues WHERE ComicID=? order by Int_IssueNumber DESC', [ComicID])
        isCounts = {}
        isCounts[1] = 0   #1 skipped
        isCounts[2] = 0   #2 wanted
        isCounts[3] = 0   #3 archived
        isCounts[4] = 0   #4 downloaded
        isCounts[5] = 0   #5 ignored
        isCounts[6] = 0   #6 failed
        isCounts[7] = 0   #7 snatched
        #isCounts[8] = 0   #8 read

        for curResult in issues:
            baseissues = {'skipped': 1, 'wanted': 2, 'archived': 3, 'downloaded': 4, 'ignored': 5, 'failed': 6, 'snatched': 7}
            for seas in baseissues:
                if curResult['Status'] is None:
                   continue
                else:
                    if seas in curResult['Status'].lower():
                        sconv = baseissues[seas]
                        isCounts[sconv]+=1
                        continue
        isCounts = {
                 "Skipped": str(isCounts[1]),
                 "Wanted": str(isCounts[2]),
                 "Archived": str(isCounts[3]),
                 "Downloaded": str(isCounts[4]),
                 "Ignored": str(isCounts[5]),
                 "Failed": str(isCounts[6]),
                 "Snatched": str(isCounts[7])
               }
        usethefuzzy = comic['UseFuzzy']
        allowpacks = comic['AllowPacks']
        skipped2wanted = "0"
        if usethefuzzy is None:
            usethefuzzy = "0"
        force_continuing = comic['ForceContinuing']
        if force_continuing is None:
            force_continuing = 0
        if mylar.DELETE_REMOVE_DIR is None:
            mylar.DELETE_REMOVE_DIR = 0
        if allowpacks is None:
            allowpacks = "0"
        if all([comic['Corrected_SeriesYear'] is not None, comic['Corrected_SeriesYear'] != '', comic['Corrected_SeriesYear'] != 'None']):
            if comic['Corrected_SeriesYear'] != comic['ComicYear']:
                comic['ComicYear'] = comic['Corrected_SeriesYear']

        comicConfig = {
                    "comiclocation": mylar.COMIC_LOCATION,
                    "fuzzy_year0": helpers.radio(int(usethefuzzy), 0),
                    "fuzzy_year1": helpers.radio(int(usethefuzzy), 1),
                    "fuzzy_year2": helpers.radio(int(usethefuzzy), 2),
                    "skipped2wanted": helpers.checked(skipped2wanted),
                    "force_continuing": helpers.checked(force_continuing),
                    "delete_dir": helpers.checked(mylar.DELETE_REMOVE_DIR),
                    "allow_packs": helpers.checked(int(allowpacks)),
                    "corrected_seriesyear": comic['ComicYear'],
               }
        if mylar.ANNUALS_ON:
            annuals = myDB.select("SELECT * FROM annuals WHERE ComicID=? ORDER BY ComicID, Int_IssueNumber DESC", [ComicID])
            #we need to load in the annual['ReleaseComicName'] and annual['ReleaseComicID']
            #then group by ReleaseComicID, in an attempt to create seperate tables for each different annual series.
            #this should allow for annuals, specials, one-shots, etc all to be included if desired.
            acnt = 0
            aName = []
            annuals_list = []
            annualinfo = {}
            prevcomicid = None
            for ann in annuals:
                if not any(d.get('annualComicID', None) == str(ann['ReleaseComicID']) for d in aName):
                    aName.append({"annualComicName":   ann['ReleaseComicName'],
                                  "annualComicID":     ann['ReleaseComicID']})

                annuals_list.append({"Issue_Number":      ann['Issue_Number'],
                                     "Int_IssueNumber":   ann['Int_IssueNumber'],
                                     "IssueName":         ann['IssueName'],
                                     "IssueDate":         ann['IssueDate'],
                                     "Status":            ann['Status'],
                                     "Location":          ann['Location'],
                                     "ComicID":           ann['ComicID'],
                                     "IssueID":           ann['IssueID'],
                                     "ReleaseComicID":    ann['ReleaseComicID'],
                                     "ComicName":         ann['ComicName'],
                                     "ComicSize":         ann['ComicSize'],
                                     "ReleaseComicName":  ann['ReleaseComicName'],
                                     "PrevComicID":       prevcomicid})

                prevcomicid = ann['ReleaseComicID']
                acnt+=1
            annualinfo = aName
            #annualinfo['count'] = acnt
        else:
            annuals_list = None
            aName = None
        return serve_template(templatename="comicdetails.html", title=comic['ComicName'], comic=comic, issues=issues, comicConfig=comicConfig, isCounts=isCounts, series=series, annuals=annuals_list, annualinfo=aName)
    comicDetails.exposed = True

    def searchit(self, name, issue=None, mode=None, type=None, explicit=None, serinfo=None):
        if type is None: type = 'comic'  # let's default this to comic search only for the time being (will add story arc, characters, etc later)
        else: logger.fdebug(str(type) + " mode enabled.")
        #mode dictates type of search:
        # --series     ...  search for comicname displaying all results
        # --pullseries ...  search for comicname displaying a limited # of results based on issue
        # --want       ...  individual comics
        if mode is None: mode = 'series'
        if len(name) == 0:
            raise cherrypy.HTTPRedirect("home")
        if type == 'comic' and mode == 'pullseries':
            if issue == 0:
                #if it's an issue 0, CV doesn't have any data populated yet - so bump it up one to at least get the current results.
                issue = 1
            try:
                searchresults, explicit = mb.findComic(name, mode, issue=issue)
            except TypeError:
                logger.error('Unable to perform required pull-list search for : [name: ' + name + '][issue: ' + issue + '][mode: ' + mode + ']')
                return
        elif type == 'comic' and mode == 'series':
            if name.startswith('4050-'):
                mismatch = "no"
                comicid = re.sub('4050-', '', name)
                logger.info('Attempting to add directly by ComicVineID: ' + str(comicid) + '. I sure hope you know what you are doing.')
                threading.Thread(target=importer.addComictoDB, args=[comicid, mismatch, None]).start()
                raise cherrypy.HTTPRedirect("comicDetails?ComicID=%s" % comicid)
            try:
                searchresults, explicit = mb.findComic(name, mode, issue=None, explicit=explicit)
            except TypeError:
                logger.error('Unable to perform required pull-list search for : [name: ' + name + '][mode: ' + mode + '][explicitsearch:' + str(explicit) + ']')
                return
        elif type == 'comic' and mode == 'want':
            try:
                searchresults, explicit = mb.findComic(name, mode, issue)
            except TypeError:
                logger.error('Unable to perform required one-off pull-list search for : [name: ' + name + '][issue: ' + issue + '][mode: ' + mode + ']')
                return
        elif type == 'story_arc':
            try:
                searchresults, explicit = mb.findComic(name, mode=None, issue=None, explicit='explicit', type='story_arc')
            except TypeError:
                logger.error('Unable to perform required story-arc search for : [arc: ' + name + '][mode: ' + mode + '][explicitsearch: explicit]')
                return

        searchresults = sorted(searchresults, key=itemgetter('comicyear', 'issues'), reverse=True)
        #print ("Results: " + str(searchresults))
        return serve_template(templatename="searchresults.html", title='Search Results for: "' + name + '"', searchresults=searchresults, type=type, imported=None, ogcname=None, name=name, explicit=explicit, serinfo=serinfo)
    searchit.exposed = True

    def addComic(self, comicid, comicname=None, comicyear=None, comicimage=None, comicissues=None, comicpublisher=None, imported=None, ogcname=None, serinfo=None):
        myDB = db.DBConnection()
        if imported == "confirm":
            # if it's coming from the importer and it's just for confirmation, record the right selection and break.
            # if it's 'confirmed' coming in as the value for imported
            # the ogcname will be the original comicid that is either correct/incorrect (doesn't matter which)
            #confirmedid is the selected series (comicid) with the letter C at the beginning to denote Confirmed.
            # then sql the original comicid which will hit on all the results for the given series.
            # iterate through, and overwrite the existing watchmatch with the new chosen 'C' + comicid value

            confirmedid = "C" + str(comicid)
            confirms = myDB.select("SELECT * FROM importresults WHERE WatchMatch=?", [ogcname])
            if confirms is None:
                logger.Error("There are no results that match...this is an ERROR.")
            else:
                for confirm in confirms:
                    controlValue = {"impID":    confirm['impID']}
                    newValue = {"WatchMatch":   str(confirmedid)}
                    myDB.upsert("importresults", newValue, controlValue)
                self.importResults()
            return
        elif imported == 'futurecheck':
            print 'serinfo:' + str(serinfo)
            logger.info('selected comicid of : ' + str(comicid) + ' [ ' + comicname + ' (' + str(comicyear) + ') ]')
            ser = []
            ser.append({"comicname": comicname,
                        "comicyear": comicyear,
                        "comicissues": comicissues,
                        "comicpublisher": comicpublisher,
                        "IssueDate": serinfo[0]['IssueDate'],
                        "IssueNumber": serinfo[0]['IssueNumber']})
            weeklypull.future_check_add(comicid, ser)
        sresults = []
        cresults = []
        mismatch = "no"
        #print ("comicid: " + str(comicid))
        #print ("comicname: " + str(comicname))
        #print ("comicyear: " + str(comicyear))
        #print ("comicissues: " + str(comicissues))
        #print ("comicimage: " + str(comicimage))
        if not mylar.CV_ONLY:
        #here we test for exception matches (ie. comics spanning more than one volume, known mismatches, etc).
            CV_EXcomicid = myDB.selectone("SELECT * from exceptions WHERE ComicID=?", [comicid]).fetchone()
            if CV_EXcomicid is None: # pass #
                gcdinfo=parseit.GCDScraper(comicname, comicyear, comicissues, comicid, quickmatch="yes")
                if gcdinfo == "No Match":
                #when it no matches, the image will always be blank...let's fix it.
                    cvdata = mylar.cv.getComic(comicid, 'comic')
                    comicimage = cvdata['ComicImage']
                    updater.no_searchresults(comicid)
                    nomatch = "true"
                    u_comicname = comicname.encode('utf-8').strip()
                    logger.info("I couldn't find an exact match for " + u_comicname + " (" + str(comicyear) + ") - gathering data for Error-Checking screen (this could take a minute)...")
                    i = 0
                    loopie, cnt = parseit.ComChk(comicname, comicyear, comicpublisher, comicissues, comicid)
                    logger.info("total count : " + str(cnt))
                    while (i < cnt):
                        try:
                            stoopie = loopie['comchkchoice'][i]
                        except (IndexError, TypeError):
                            break
                        cresults.append({
                               'ComicID':   stoopie['ComicID'],
                               'ComicName':   stoopie['ComicName'].decode('utf-8', 'replace'),
                               'ComicYear':   stoopie['ComicYear'],
                               'ComicIssues': stoopie['ComicIssues'],
                               'ComicURL':    stoopie['ComicURL'],
                               'ComicPublisher': stoopie['ComicPublisher'].decode('utf-8', 'replace'),
                               'GCDID': stoopie['GCDID']
                               })
                        i+=1
                    if imported != 'None':
                    #if it's from an import and it has to go through the UEC, return the values
                    #to the calling function and have that return the template
                        return cresults
                    else:
                        return serve_template(templatename="searchfix.html", title="Error Check", comicname=comicname, comicid=comicid, comicyear=comicyear, comicimage=comicimage, comicissues=comicissues, cresults=cresults, imported=None, ogcname=None)
                else:
                    nomatch = "false"
                    logger.info(u"Quick match success..continuing.")
            else:
                if CV_EXcomicid['variloop'] == '99':
                    logger.info(u"mismatched name...autocorrecting to correct GID and auto-adding.")
                    mismatch = "yes"
                if CV_EXcomicid['NewComicID'] == 'none':
                    logger.info(u"multi-volume series detected")
                    testspx = CV_EXcomicid['GComicID'].split('/')
                    for exc in testspx:
                        fakeit = parseit.GCDAdd(testspx)
                        howmany = int(CV_EXcomicid['variloop'])
                        t = 0
                        while (t <= howmany):
                            try:
                                sres = fakeit['serieschoice'][t]
                            except IndexError:
                                break
                            sresults.append({
                                   'ComicID':   sres['ComicID'],
                                   'ComicName':   sres['ComicName'],
                                   'ComicYear':   sres['ComicYear'],
                                   'ComicIssues': sres['ComicIssues'],
                                   'ComicPublisher': sres['ComicPublisher'],
                                   'ComicCover':    sres['ComicCover']
                                   })
                            t+=1
                        #searchfix(-1).html is for misnamed comics and wrong years.
                        #searchfix-2.html is for comics that span multiple volumes.
                        return serve_template(templatename="searchfix-2.html", title="In-Depth Results", sresults=sresults)
        #print ("imported is: " + str(imported))
        threading.Thread(target=importer.addComictoDB, args=[comicid, mismatch, None, imported, ogcname]).start()
        raise cherrypy.HTTPRedirect("comicDetails?ComicID=%s" % comicid)
    addComic.exposed = True

    def addbyid(self, comicid, calledby=None, imported=None, ogcname=None):
        mismatch = "no"
        logger.info('Attempting to add directly by ComicVineID: ' + str(comicid))
        if comicid.startswith('4050-'): comicid = re.sub('4050-', '', comicid)
        threading.Thread(target=importer.addComictoDB, args=[comicid, mismatch, None, imported, ogcname]).start()
        if calledby == True or calledby == 'True':
           return
        elif calledby == 'web-import':
           raise cherrypy.HTTPRedirect("importResults")
        else:
           raise cherrypy.HTTPRedirect("comicDetails?ComicID=%s" % comicid)
    addbyid.exposed = True

    def addStoryArc_thread(self, **kwargs):
        threading.Thread(target=self.addStoryArc, kwargs=kwargs).start()
    addStoryArc_thread.exposed = True

    def addStoryArc(self, arcid, arcrefresh=False, cvarcid=None, arclist=None, storyarcname=None, storyarcyear=None, storyarcpublisher=None, storyarcissues=None, desc=None, image=None):
        # used when a choice is selected to 'add story arc' via the searchresults screen (via the story arc search).
        # arclist contains ALL the issueid's in sequence, along with the issue titles.
        # call the function within cv.py to grab all the issueid's and return all the issue data
        module = '[STORY ARC]'
        myDB = db.DBConnection()
        #check if it already exists.
        if cvarcid is None:
            arc_chk = myDB.select('SELECT * FROM readinglist WHERE StoryArcID=?', [arcid])
        else:
            arc_chk = myDB.select('SELECT * FROM readinglist WHERE CV_ArcID=?', [cvarcid])
        if arc_chk is None:
            if arcrefresh:
                logger.warn(module + ' Unable to retrieve Story Arc ComicVine ID from the db. Unable to refresh Story Arc at this time. You probably have to delete/readd the story arc this one time for Refreshing to work properly.')
                return
            else:
                logger.fdebug(module + ' No match in db based on ComicVine ID. Making sure and checking against Story Arc Name.')
                arc_chk = myDB.select('SELECT * FROM readinglist WHERE StoryArc=?', [storyarcname])
                if arc_chk is None:
                    logger.warn(module + ' ' + storyarcname + ' already exists on your Story Arc Watchlist!')
                    raise cherrypy.HTTPRedirect("readlist")
        else:
            if arcrefresh: #cvarcid must be present here as well..
                logger.info(module + '[' + str(arcid) + '] Successfully found Story Arc ComicVine ID [4045-' + str(cvarcid) + '] within db. Preparing to refresh Story Arc.')
                # we need to store the existing arc values that are in the db, so we don't create duplicate entries or mess up items.
                iss_arcids = []
                for issarc in arc_chk:
                    iss_arcids.append({"IssueArcID":  issarc['IssueArcID'],
                                       "IssueID":     issarc['IssueID']})
                arcinfo = mb.storyarcinfo(cvarcid)
                if len(arcinfo) > 1:
                    arclist = arcinfo['arclist']
                else:
                    logger.warn(module + ' Unable to retrieve issue details at this time. Something is probably wrong.')
                    return
#            else:
#                logger.warn(module + ' ' + storyarcname + ' already exists on your Story Arc Watchlist.')
#                raise cherrypy.HTTPRedirect("readlist")
        arc_results = mylar.cv.getComic(comicid=None, type='issue', arcid=arcid, arclist=arclist)
        logger.fdebug(module + ' Arcresults: ' + str(arc_results))
        logger.fdebug('arclist: ' + str(arclist))
        if len(arc_results) > 0:
            import random

            issuedata = []
            if storyarcissues is None:
                storyarcissues = len(arc_results['issuechoice'])
            if arcid is None:
                storyarcid = str(random.randint(1000,9999)) + str(storyarcissues)
            else:
                storyarcid = arcid
            n = 0
            cidlist = ''
            iscnt = int(storyarcissues)
            while (n <= iscnt):
                try:
                    arcval = arc_results['issuechoice'][n]
                except IndexError:
                    break
                comicname = arcval['ComicName']
                st_d = mylar.filechecker.FileChecker(watchcomic=comicname)
                st_dyninfo = st_d.dynamic_replace(comicname)
                dynamic_name = re.sub('[\|\s]','', st_dyninfo['mod_seriesname'].lower()).strip()

                issname = arcval['Issue_Name']
                issid = str(arcval['IssueID'])
                comicid = str(arcval['ComicID'])
                if comicid not in cidlist:
                    if n == 0:
                        cidlist += str(comicid)
                    else:
                        cidlist += '|' + str(comicid)
                #don't recreate the st_issueid if it's a refresh and the issueid already exists (will create duplicates otherwise)
                st_issueid = None
                if arcrefresh:
                    for aid in iss_arcids:
                        if aid['IssueID'] == issid:
                            st_issueid = aid['IssueArcID']
                if st_issueid is None:
                    st_issueid = str(storyarcid) + "_" + str(random.randint(1000,9999))
                issnum = arcval['Issue_Number']
                issdate = str(arcval['Issue_Date'])
                storedate = str(arcval['Store_Date'])

                int_issnum = helpers.issuedigits(issnum)

                #verify the reading order if present.
                findorder = arclist.find(issid)
                if findorder != -1:
                    ros = arclist.find('|',findorder+1)
                    if ros != -1:
                        roslen = arclist[findorder:ros]
                    else:
                        #last entry doesn't have a trailling '|'
                        roslen = arclist[findorder:]
                    rosre = re.sub(issid,'', roslen)
                    readingorder = int(re.sub('[\,\|]','', rosre).strip())
                else:
                    readingorder = 0
                logger.fdebug('[' + str(readingorder) + '] issueid:' + str(issid) + ' - findorder#:' + str(findorder))

                issuedata.append({"ComicID":            comicid,
                                  "IssueID":            issid,
                                  "StoryArcID":         storyarcid,
                                  "IssueArcID":         st_issueid,
                                  "ComicName":          comicname,
                                  "DynamicName":        dynamic_name,
                                  "IssueName":          issname,
                                  "Issue_Number":       issnum,
                                  "IssueDate":          issdate,
                                  "ReleaseDate":        storedate,
                                  "ReadingOrder":       readingorder, #n +1,
                                  "Int_IssueNumber":    int_issnum})
                n+=1

            comicid_results = mylar.cv.getComic(comicid=None, type='comicyears', comicidlist=cidlist)
            logger.fdebug(module + ' Initiating issue updating - just the info')

            for AD in issuedata:
                seriesYear = 'None'
                issuePublisher = 'None'
                seriesVolume = 'None'

                if AD['IssueName'] is None:
                    IssueName = 'None'
                else:
                    IssueName = AD['IssueName'][:70]

                for cid in comicid_results:
                    if cid['ComicID'] == AD['ComicID']:
                        seriesYear = cid['SeriesYear']
                        issuePublisher = cid['Publisher']
                        seriesVolume = cid['Volume']
                        if storyarcpublisher is None:
                            #assume that the arc is the same
                            storyarcpublisher = issuePublisher
                        break

                newCtrl = {"IssueID":           AD['IssueID'],
                           "StoryArcID":        AD['StoryArcID']}
                newVals = {"ComicID":           AD['ComicID'],
                           "IssueArcID":        AD['IssueArcID'],
                           "StoryArc":          storyarcname,
                           "ComicName":         AD['ComicName'],
                           "Volume":            seriesVolume,
                           "DynamicComicName":  AD['DynamicName'],
                           "IssueName":         IssueName,
                           "IssueNumber":       AD['Issue_Number'],
                           "Publisher":         storyarcpublisher,
                           "TotalIssues":       storyarcissues,
                           "ReadingOrder":      AD['ReadingOrder'],
                           "IssueDate":         AD['IssueDate'],
                           "StoreDate":         AD['ReleaseDate'],
                           "SeriesYear":        seriesYear,
                           "IssuePublisher":    issuePublisher,
                           "CV_ArcID":          arcid,
                           "Int_IssueNumber":   AD['Int_IssueNumber']}

                myDB.upsert("readinglist", newVals, newCtrl)

        logger.info(newVals)
        #run the Search for Watchlist matches now.
        logger.fdebug(module + ' Now searching your watchlist for matches belonging to this story arc.')
        self.ArcWatchlist(storyarcid)
        if arcrefresh:
            return
        else:
            raise cherrypy.HTTPRedirect("detailStoryArc?StoryArcID=%s&StoryArcName=%s" % (storyarcid, storyarcname))
    addStoryArc.exposed = True

    def wanted_Export(self,mode):
        import unicodedata
        myDB = db.DBConnection()
        wantlist = myDB.select("SELECT * FROM issues WHERE Status=? AND ComicName NOT NULL", [mode])
        if wantlist is None:
            logger.info("There aren't any issues marked as " + mode + ". Aborting Export.")
            return
        #write it a wanted_list.csv
        logger.info("gathered data - writing to csv...")
        except_file = os.path.join(mylar.DATA_DIR, str(mode) + "_list.csv")
        if os.path.exists(except_file):
            try:
                 os.remove(except_file)
            except (OSError, IOError):
                pass

        wcount=0

        with open(str(except_file), 'w+') as f:
            headrow = "SeriesName,SeriesYear,IssueNumber,IssueDate,ComicID,IssueID"
            headerline = headrow.decode('utf-8', 'ignore')
            f.write('%s\n' % (headerline.encode('ascii', 'replace').strip()))
            for want in wantlist:
                wantcomic = myDB.selectone("SELECT * FROM comics WHERE ComicID=?", [want['ComicID']]).fetchone()
                exceptln = wantcomic['ComicName'].encode('ascii', 'replace') + "," + str(wantcomic['ComicYear']) + "," + str(want['Issue_Number']) + "," + str(want['IssueDate']) + "," + str(want['ComicID']) + "," + str(want['IssueID'])
                #logger.fdebug(exceptln)
                wcount+=1
                f.write('%s\n' % (exceptln.encode('ascii', 'replace').strip()))

        logger.info("Successfully wrote to csv file " + str(wcount) + " entries from your " + mode + " list.")

        raise cherrypy.HTTPRedirect("home")
    wanted_Export.exposed = True

    def from_Exceptions(self, comicid, gcdid, comicname=None, comicyear=None, comicissues=None, comicpublisher=None, imported=None, ogcname=None):
        import unicodedata
        mismatch = "yes"
        #write it to the custom_exceptions.csv and reload it so that importer will pick it up and do it's thing :)
        #custom_exceptions in this format...
        #99, (comicid), (gcdid), none
        logger.info("saving new information into custom_exceptions.csv...")
        except_info = "none #" + str(comicname) + "-(" + str(comicyear) + ")\n"
        except_file = os.path.join(mylar.DATA_DIR, "custom_exceptions.csv")
        if not os.path.exists(except_file):
            try:
                 csvfile = open(str(except_file), 'rb')
                 csvfile.close()
            except (OSError, IOError):
                logger.error("Could not locate " + str(except_file) + " file. Make sure it's in datadir: " + mylar.DATA_DIR + " with proper permissions.")
                return
        exceptln = "99," + str(comicid) + "," + str(gcdid) + "," + str(except_info)
        exceptline = exceptln.decode('utf-8', 'ignore')

        with open(str(except_file), 'a') as f:
           #f.write('%s,%s,%s,%s\n' % ("99", comicid, gcdid, except_info)
            f.write('%s\n' % (exceptline.encode('ascii', 'replace').strip()))
        logger.info("re-loading csv file so it's all nice and current.")
        mylar.csv_load()
        if imported:
            threading.Thread(target=importer.addComictoDB, args=[comicid, mismatch, None, imported, ogcname]).start()
        else:
            threading.Thread(target=importer.addComictoDB, args=[comicid, mismatch]).start()
        raise cherrypy.HTTPRedirect("comicDetails?ComicID=%s" % comicid)
    from_Exceptions.exposed = True

    def GCDaddComic(self, comicid, comicname=None, comicyear=None, comicissues=None, comiccover=None, comicpublisher=None):
        #since we already know most of the info, let's add it to the db so we can reference it later.
        myDB = db.DBConnection()
        gcomicid = "G" + str(comicid)
        comicyear_len = comicyear.find(' ', 2)
        comyear = comicyear[comicyear_len +1:comicyear_len +5]
        if comyear.isdigit():
            logger.fdebug("Series year set to : " + str(comyear))
        else:
            logger.fdebug("Invalid Series year detected - trying to adjust from " + str(comyear))
            #comicyear_len above will trap wrong year if it's 10 October 2010 - etc ( 2000 AD)...
            find_comicyear = comicyear.split()
            for i in find_comicyear:
                if len(i) == 4:
                    logger.fdebug("Series year detected as : " + str(i))
                    comyear = str(i)
                    continue

            logger.fdebug("Series year set to: " + str(comyear))

        controlValueDict = {'ComicID': gcomicid}
        newValueDict = {'ComicName': comicname,
                        'ComicYear': comyear,
                        'ComicPublished': comicyear,
                        'ComicPublisher': comicpublisher,
                        'ComicImage': comiccover,
                        'Total': comicissues}
        myDB.upsert("comics", newValueDict, controlValueDict)
        threading.Thread(target=importer.GCDimport, args=[gcomicid]).start()
        raise cherrypy.HTTPRedirect("comicDetails?ComicID=%s" % gcomicid)
    GCDaddComic.exposed = True

    def post_process(self, nzb_name, nzb_folder, failed=False, apc_version=None, comicrn_version=None):
        if all([nzb_name != 'Manual Run', nzb_name != 'Manual+Run']):
            if comicrn_version is None and apc_version is None:
                logger.warn('ComicRN should be v' + str(mylar.STATIC_COMICRN_VERSION) + ' and autoProcessComics.py should be v' + str(mylar.STATIC_APC_VERSION) + ', but they are not and are out of date. Post-Processing may or may not work.')
            elif comicrn_version is None or comicrn_version != mylar.STATIC_COMICRN_VERSION:
                if comicrn_version == 'None':
                    comicrn_version = "0"
                logger.warn('Your ComicRN.py script should be v' + str(mylar.STATIC_COMICRN_VERSION) + ', but is v' + str(comicrn_version) + ' and is out of date. Things may still work - but you are taking your chances.')
            elif apc_version is None or apc_version != mylar.STATIC_APC_VERSION:
                if apc_version == 'None':
                    apc_version = "0"
                logger.warn('Your autoProcessComics.py script should be v' + str(mylar.STATIC_APC_VERSION) + ', but is v' + str(apc_version) + ' and is out of date. Odds are something is gonna fail - you should update it.')
            else:
                logger.info('ComicRN.py version: ' + str(comicrn_version) + ' -- autoProcessComics.py version: ' + str(apc_version))

        import Queue
        logger.info('Starting postprocessing for : ' + nzb_name)
        if failed == '0':
            failed = False
        elif failed == '1':
            failed = True

        queue = Queue.Queue()
        retry_outside = False

        if not failed:
            PostProcess = PostProcessor.PostProcessor(nzb_name, nzb_folder, queue=queue)
            if nzb_name == 'Manual Run' or nzb_name == 'Manual+Run':
                threading.Thread(target=PostProcess.Process).start()
                #raise cherrypy.HTTPRedirect("home")
            else:
                thread_ = threading.Thread(target=PostProcess.Process, name="Post-Processing")
                thread_.start()
                thread_.join()
                chk = queue.get()
                while True:
                    if chk[0]['mode'] == 'fail':
                        yield chk[0]['self.log']
                        logger.info('Initiating Failed Download handling')
                        if chk[0]['annchk'] == 'no': mode = 'want'
                        else: mode = 'want_ann'
                        failed = True
                        break
                    elif chk[0]['mode'] == 'stop':
                        yield chk[0]['self.log']
                        break
                    elif chk[0]['mode'] == 'outside':
                        yield chk[0]['self.log']
                        retry_outside = True
                        break
                    else:
                        logger.error('mode is unsupported: ' + chk[0]['mode'])
                        yield chk[0]['self.log']
                        break

        if failed:
            if mylar.FAILED_DOWNLOAD_HANDLING:
                #drop the if-else continuation so we can drop down to this from the above if statement.
                logger.info('Initiating Failed Download handling for this download.')
                FailProcess = Failed.FailedProcessor(nzb_name=nzb_name, nzb_folder=nzb_folder, queue=queue)
                thread_ = threading.Thread(target=FailProcess.Process, name="FAILED Post-Processing")
                thread_.start()
                thread_.join()
                failchk = queue.get()
                if failchk[0]['mode'] == 'retry':
                    yield failchk[0]['self.log']
                    logger.info('Attempting to return to search module with ' + str(failchk[0]['issueid']))
                    if failchk[0]['annchk'] == 'no': mode = 'want'
                    else: mode = 'want_ann'
                    self.queueit(mode=mode, ComicName=failchk[0]['comicname'], ComicIssue=failchk[0]['issuenumber'], ComicID=failchk[0]['comicid'], IssueID=failchk[0]['issueid'], manualsearch=True)
                elif failchk[0]['mode'] == 'stop':
                    yield failchk[0]['self.log']
                else:
                    logger.error('mode is unsupported: ' + failchk[0]['mode'])
                    yield failchk[0]['self.log']
            else:
                logger.warn('Failed Download Handling is not enabled. Leaving Failed Download as-is.')

        if retry_outside:
            PostProcess = PostProcessor.PostProcessor('Manual Run', nzb_folder, queue=queue)
            thread_ = threading.Thread(target=PostProcess.Process, name="Post-Processing")
            thread_.start()
            thread_.join()
            chk = queue.get()
            while True:
                if chk[0]['mode'] == 'fail':
                    yield chk[0]['self.log']
                    logger.info('Initiating Failed Download handling')
                    if chk[0]['annchk'] == 'no': mode = 'want'
                    else: mode = 'want_ann'
                    failed = True
                    break
                elif chk[0]['mode'] == 'stop':
                    yield chk[0]['self.log']
                    break
                else:
                    logger.error('mode is unsupported: ' + chk[0]['mode'])
                    yield chk[0]['self.log']
                    break

    post_process.exposed = True

    def pauseSeries(self, ComicID):
        logger.info(u"Pausing comic: " + ComicID)
        myDB = db.DBConnection()
        controlValueDict = {'ComicID': ComicID}
        newValueDict = {'Status': 'Paused'}
        myDB.upsert("comics", newValueDict, controlValueDict)
        raise cherrypy.HTTPRedirect("comicDetails?ComicID=%s" % ComicID)
    pauseSeries.exposed = True

    def resumeSeries(self, ComicID):
        logger.info(u"Resuming comic: " + ComicID)
        myDB = db.DBConnection()
        controlValueDict = {'ComicID': ComicID}
        newValueDict = {'Status': 'Active'}
        myDB.upsert("comics", newValueDict, controlValueDict)
        raise cherrypy.HTTPRedirect("comicDetails?ComicID=%s" % ComicID)
    resumeSeries.exposed = True

    def deleteSeries(self, ComicID, delete_dir=None):
        myDB = db.DBConnection()
        comic = myDB.selectone('SELECT * from comics WHERE ComicID=?', [ComicID]).fetchone()
        if comic['ComicName'] is None: ComicName = "None"
        else: ComicName = comic['ComicName']
        seriesdir = comic['ComicLocation']
        logger.info(u"Deleting all traces of Comic: " + ComicName)
        myDB.action('DELETE from comics WHERE ComicID=?', [ComicID])
        myDB.action('DELETE from issues WHERE ComicID=?', [ComicID])
        if mylar.ANNUALS_ON:
            myDB.action('DELETE from annuals WHERE ComicID=?', [ComicID])
        myDB.action('DELETE from upcoming WHERE ComicID=?', [ComicID])
        if delete_dir: #mylar.DELETE_REMOVE_DIR:
            logger.fdebug('Remove directory on series removal enabled.')
            if os.path.exists(seriesdir):
                logger.fdebug('Attempting to remove the directory and contents of : ' + seriesdir)
                try:
                    shutil.rmtree(seriesdir)
                except:
                    logger.warn('Unable to remove directory after removing series from Mylar.')
            else:
                logger.warn('Unable to remove directory as it does not exist in : ' + seriesdir)
            myDB.action('DELETE from readlist WHERE ComicID=?', [ComicID])

        helpers.ComicSort(sequence='update')
        if mylar.SAFESTART:
            raise cherrypy.HTTPRedirect("manageComics")
        else:
            raise cherrypy.HTTPRedirect("home")
    deleteSeries.exposed = True

    def wipenzblog(self, ComicID=None, IssueID=None):
        myDB = db.DBConnection()
        if ComicID is None:
            logger.fdebug("Wiping NZBLOG in it's entirety. You should NOT be downloading while doing this or else you'll lose the log for the download.")
            myDB.action('DROP table nzblog')
            logger.fdebug("Deleted nzblog table.")
            myDB.action('CREATE TABLE IF NOT EXISTS nzblog (IssueID TEXT, NZBName TEXT, SARC TEXT, PROVIDER TEXT, ID TEXT, AltNZBName TEXT)')
            logger.fdebug("Re-created nzblog table.")
            raise cherrypy.HTTPRedirect("history")
        if IssueID:
            logger.fdebug('Removing all download history for the given IssueID. This should allow post-processing to finish for the given IssueID.')
            myDB.action('DELETE FROM nzblog WHERE IssueID=?', [IssueID])
            logger.fdebug('Successfully removed all entries in the download log for IssueID: ' + str(IssueID))
            raise cherrypy.HTTPRedirect("history")
    wipenzblog.exposed = True

    def refreshSeries(self, ComicID):
        comicsToAdd = [ComicID]
        logger.fdebug("Refreshing comic: %s" % comicsToAdd)
        threading.Thread(target=updater.dbUpdate, args=[comicsToAdd]).start()
    refreshSeries.exposed = True

    def refreshArtist(self, ComicID):
        myDB = db.DBConnection()
        mismatch = "no"
        logger.fdebug('Refreshing comicid: ' + str(ComicID))
        if not mylar.CV_ONLY or ComicID[:1] == "G":

            CV_EXcomicid = myDB.selectone("SELECT * from exceptions WHERE ComicID=?", [ComicID]).fetchone()
            if CV_EXcomicid is None: pass
            else:
                if CV_EXcomicid['variloop'] == '99':
                    mismatch = "yes"
            if ComicID[:1] == "G": threading.Thread(target=importer.GCDimport, args=[ComicID]).start()
            else: threading.Thread(target=importer.addComictoDB, args=[ComicID, mismatch]).start()
        else:
            if mylar.CV_ONETIMER == 1:
                logger.fdebug("CV_OneTimer option enabled...")
                #in order to update to JUST CV_ONLY, we need to delete the issues for a given series so it's a clean grab.
                logger.fdebug("Gathering the status of all issues for the series.")

                issues = myDB.select('SELECT * FROM issues WHERE ComicID=?', [ComicID])

                if not issues:
                    #if issues are None it's probably a bad refresh/maxed out API that resulted in the issue data
                    #getting wiped out and not refreshed. Setting whack=True will force a complete refresh.
                    logger.info('No issue data available. This is Whack.')
                    whack = True
                else:
                    #check for series that are numerically out of whack (ie. 5/4)
                    logger.info('Checking how out of whack the series is.')
                    whack = helpers.havetotals(refreshit=ComicID)


                annload = []  #initiate the list here so we don't error out below.

                if mylar.ANNUALS_ON:
                    #now we load the annuals into memory to pass through to importer when refreshing so that it can
                    #refresh even the manually added annuals.
                    annual_load = myDB.select('SELECT * FROM annuals WHERE ComicID=?', [ComicID])
                    logger.fdebug('checking annual db')
                    for annthis in annual_load:
                        if not any(d['ReleaseComicID'] == annthis['ReleaseComicID'] for d in annload):
                            annload.append({
                                  'ReleaseComicID':   annthis['ReleaseComicID'],
                                  'ReleaseComicName': annthis['ReleaseComicName'],
                                  'ComicID':          annthis['ComicID'],
                                  'ComicName':        annthis['ComicName']
                                  })
                    issues += annual_load #myDB.select('SELECT * FROM annuals WHERE ComicID=?', [ComicID])
                #store the issues' status for a given comicid, after deleting and readding, flip the status back to$
                logger.fdebug("Deleting all issue data.")
                myDB.action('DELETE FROM issues WHERE ComicID=?', [ComicID])
                myDB.action('DELETE FROM annuals WHERE ComicID=?', [ComicID])
                logger.fdebug("Refreshing the series and pulling in new data using only CV.")
                if whack == False:
                    cchk = mylar.importer.addComictoDB(ComicID, mismatch, calledfrom='dbupdate', annload=annload)
                    #reload the annuals here.

                    issues_new = myDB.select('SELECT * FROM issues WHERE ComicID=?', [ComicID])
                    annuals = []
                    ann_list = []
                    if mylar.ANNUALS_ON:
                        annuals_list = myDB.select('SELECT * FROM annuals WHERE ComicID=?', [ComicID])
                        ann_list += annuals_list
                        issues_new += annuals_list

                    logger.fdebug("Attempting to put the Status' back how they were.")
                    icount = 0
                    #the problem - the loop below will not match on NEW issues that have been refreshed that weren't present in the
                    #db before (ie. you left Mylar off for abit, and when you started it up it pulled down new issue information)
                    #need to test if issuenew['Status'] is None, but in a seperate loop below.
                    fndissue = []
                    for issue in issues:
                        for issuenew in issues_new:
                            #logger.fdebug(str(issue['Issue_Number']) + ' - issuenew:' + str(issuenew['IssueID']) + ' : ' + str(issuenew['Status']))
                            #logger.fdebug(str(issue['Issue_Number']) + ' - issue:' + str(issue['IssueID']) + ' : ' + str(issue['Status']))
                            if issuenew['IssueID'] == issue['IssueID'] and issuenew['Status'] != issue['Status']:
                                ctrlVAL = {"IssueID":      issue['IssueID']}
                                #if the status is None and the original status is either Downloaded / Archived, keep status & stats
                                if issuenew['Status'] == None and (issue['Status'] == 'Downloaded' or issue['Status'] == 'Archived'):
                                    newVAL = {"Location":     issue['Location'],
                                              "ComicSize":    issue['ComicSize'],
                                              "Status":       issue['Status']}
                                #if the status is now Downloaded/Snatched, keep status & stats (downloaded only)
                                elif issuenew['Status'] == 'Downloaded' or issue['Status'] == 'Snatched':
                                    newVAL = {"Location":      issue['Location'],
                                              "ComicSize":     issue['ComicSize']}
                                    if issuenew['Status'] == 'Downloaded':
                                        newVAL['Status'] = issuenew['Status']
                                    else:
                                        newVAL['Status'] = issue['Status']

                                elif issue['Status'] == 'Archived':
                                    newVAL = {"Status":        issue['Status'],
                                              "Location":      issue['Location'],
                                              "ComicSize":     issue['ComicSize']}
                                else:
                                    #change the status to the previous status
                                    newVAL = {"Status":        issue['Status']}

                                if newVAL['Status'] == None:
                                    newVAL = {"Status":        "Skipped"}

                                if any(d['IssueID'] == str(issue['IssueID']) for d in ann_list):
                                    logger.fdebug("annual detected for " + str(issue['IssueID']) + " #: " + str(issue['Issue_Number']))
                                    myDB.upsert("Annuals", newVAL, ctrlVAL)
                                else:
                                    #logger.fdebug('#' + str(issue['Issue_Number']) + ' writing issuedata: ' + str(newVAL))
                                    myDB.upsert("Issues", newVAL, ctrlVAL)
                                fndissue.append({"IssueID":      issue['IssueID']})
                                icount+=1
                                break
                    logger.info("In the process of converting the data to CV, I changed the status of " + str(icount) + " issues.")

                    issues_new = myDB.select('SELECT * FROM issues WHERE ComicID=? AND Status is NULL', [ComicID])
                    if mylar.ANNUALS_ON:
                        issues_new += myDB.select('SELECT * FROM annuals WHERE ComicID=? AND Status is NULL', [ComicID])

                    newiss = []
                    if mylar.AUTOWANT_UPCOMING:
                        #only mark store date >= current date as Wanted.
                        newstatus = "Wanted"
                    else:
                        newstatus = "Skipped"
                    for iss in issues_new:
                         newiss.append({"IssueID":      iss['IssueID'],
                                        "Status":       newstatus})
                    if len(newiss) > 0:
                         for newi in newiss:
                             ctrlVAL = {"IssueID":   newi['IssueID']}
                             newVAL = {"Status":     newi['Status']}
                             #logger.info('writing issuedata: ' + str(newVAL))
                             myDB.upsert("Issues", newVAL, ctrlVAL)

                    logger.info('I have added ' + str(len(newiss)) + ' new issues for this series that were not present before.')
                else:
                    cchk = mylar.importer.addComictoDB(ComicID, mismatch, annload=annload)

            else:
                cchk = mylar.importer.addComictoDB(ComicID, mismatch)

        raise cherrypy.HTTPRedirect("comicDetails?ComicID=%s" % ComicID)
    refreshArtist.exposed=True

    def issue_edit(self, id, value):
        logger.fdebug('id: ' + str(id))
        logger.fdebug('value: ' + str(value))
        comicid = id[:id.find('.')]
        logger.fdebug('comicid:' + str(comicid))
        issueid = id[id.find('.') +1:]
        logger.fdebug('issueid:' + str(issueid))
        myDB = db.DBConnection()
        comicchk = myDB.selectone('SELECT ComicYear FROM comics WHERE ComicID=?', [comicid]).fetchone()
        issuechk = myDB.selectone('SELECT * FROM issues WHERE IssueID=?', [issueid]).fetchone()
        if issuechk is None:
            logger.error('Cannot edit this for some reason - something is wrong.')
            return
        oldissuedate = issuechk['IssueDate']
        seriesyear = comicchk['ComicYear']
        issuenumber = issuechk['Issue_Number']

        #check if the new date is in the correct format of yyyy-mm-dd
        try:
            valid_date = time.strptime(value, '%Y-%m-%d')
        except ValueError:
            logger.error('invalid date provided. Rejecting edit.')
            return oldissuedate

        #if the new issue year is less than the series year - reject it.
        if value[:4] < seriesyear:
            logger.error('Series year of ' + str(seriesyear) + ' is less than new issue date of ' + str(value[:4]))
            return oldissuedate

        newVal = {"IssueDate": value,
                  "IssueDate_Edit": oldissuedate}
        ctrlVal = {"IssueID": issueid}
        myDB.upsert("issues", newVal, ctrlVal)
        logger.info('Updated Issue Date for issue #' + str(issuenumber))
        return value

    issue_edit.exposed=True

    def force_rss(self):
        logger.info('Attempting to run RSS Check Forcibly')
        #forcerss = True
        #threading.Thread(target=mylar.rsscheck.tehMain, args=[True]).start()
        #this is for use with the new scheduler not in place yet.
        forcethis = mylar.rsscheckit.tehMain(forcerss=True)
        threading.Thread(target=forcethis.run).start()
        return
    force_rss.exposed = True

    def markannuals(self, ann_action=None, **args):
        self.markissues(ann_action, **args)
    markannuals.exposed = True

    def markissues(self, action=None, **args):
        myDB = db.DBConnection()
        issuesToAdd = []
        issuestoArchive = []
        if action == 'WantedNew':
            newaction = 'Wanted'
        else:
            newaction = action

        for IssueID in args:
            if any([IssueID is None, 'issue_table' in IssueID, 'history_table' in IssueID, 'manage_issues' in IssueID, 'issue_table_length' in IssueID, 'issues' in IssueID, 'annuals' in IssueID]):
                continue
            else:
                mi = myDB.selectone("SELECT * FROM issues WHERE IssueID=?", [IssueID]).fetchone()
                annchk = 'no'
                if mi is None:
                    if mylar.ANNUALS_ON:
                        mi = myDB.selectone("SELECT * FROM annuals WHERE IssueID=?", [IssueID]).fetchone()
                        comicname = mi['ReleaseComicName']
                        annchk = 'yes'
                else:
                    comicname = mi['ComicName']

                miyr = myDB.selectone("SELECT ComicYear FROM comics WHERE ComicID=?", [mi['ComicID']]).fetchone()
                if action == 'Downloaded':
                    if mi['Status'] == "Skipped" or mi['Status'] == "Wanted":
                        logger.fdebug(u"Cannot change status to %s as comic is not Snatched or Downloaded" % (newaction))
                        continue
                elif action == 'Archived':
                    logger.fdebug(u"Marking %s %s as %s" % (comicname, mi['Issue_Number'], newaction))
                    #updater.forceRescan(mi['ComicID'])
                    issuestoArchive.append(IssueID)
                elif action == 'Wanted' or action == 'Retry':
                    if action == 'Retry': newaction = 'Wanted'
                    logger.fdebug(u"Marking %s %s as %s" % (comicname, mi['Issue_Number'], newaction))
                    issuesToAdd.append(IssueID)
                elif action == 'Skipped':
                    logger.fdebug(u"Marking " + str(IssueID) + " as Skipped")
                elif action == 'Clear':
                    myDB.action("DELETE FROM snatched WHERE IssueID=?", [IssueID])
                elif action == 'Failed' and mylar.FAILED_DOWNLOAD_HANDLING:
                    logger.fdebug('Marking [' + comicname + '] : ' + str(IssueID) + ' as Failed. Sending to failed download handler.')
                    failedcomicid = mi['ComicID']
                    failedissueid = IssueID
                    break
                controlValueDict = {"IssueID": IssueID}
                newValueDict = {"Status": newaction}
                if annchk == 'yes':
                    myDB.upsert("annuals", newValueDict, controlValueDict)
                else:
                    myDB.upsert("issues", newValueDict, controlValueDict)
                logger.fdebug("updated...to " + str(newaction))
        if action == 'Failed' and mylar.FAILED_DOWNLOAD_HANDLING:
            self.failed_handling(failedcomicid, failedissueid)
        if len(issuestoArchive) > 0:
            updater.forceRescan(mi['ComicID'])
        if len(issuesToAdd) > 0:
            logger.fdebug("Marking issues: %s as Wanted" % (issuesToAdd))
            threading.Thread(target=search.searchIssueIDList, args=[issuesToAdd]).start()

        #raise cherrypy.HTTPRedirect("comicDetails?ComicID=%s" % mi['ComicID'])
    markissues.exposed = True

    def markentries(self, action=None, **args):
        myDB = db.DBConnection()
        cnt = 0
        for ID in args:
            logger.info(ID)
            if any([ID is None, 'manage_failed_length' in ID]):
                continue
            else:
                myDB.action("DELETE FROM Failed WHERE ID=?", [ID])
                cnt+=1
        logger.info('[DB FAILED CLEANSING] Cleared ' + str(cnt) + ' entries from the Failed DB so they will now be downloaded if available/working.')
    markentries.exposed = True

    def retryit(self, **kwargs):
        threading.Thread(target=self.retryissue, kwargs=kwargs).start()
    retryit.exposed = True

    def retryissue(self, ComicName, ComicID, IssueID, IssueNumber, ReleaseComicID=None, ComicYear=None, redirect=None):

        logger.info('ComicID:' + str(ComicID))
        logger.info('Retrying : ' + str(IssueID))
        # mode = either series or annual (want vs. want_ann)
        #To retry the exact download again - we already have the nzb/torrent name stored in the nzblog.
        #0 - Change status to Retrying.
        #1 - we need to search the snatched table for the relevant information (since it HAS to be in snatched status)
        #2 - we need to reference the ID from the snatched table to the nzblog table
        #  - if it doesn't match, then it's an invalid retry.
        #  - if it does match, we get the nzbname/torrent name and provider info
        #3 - if it's an nzb - we recreate the sab/nzbget url and resubmit it directly.
        #  - if it's a torrent - we redownload the torrent and flip it to the watchdir on the local / seedbox.
        #4 - Change status to Snatched.
        myDB = db.DBConnection()
        chk_snatch = myDB.select('SELECT * FROM snatched WHERE IssueID=?', [IssueID])
        if chk_snatch is None:
            logger.info('Unable to locate how issue was downloaded (name, provider). Cannot continue.')
            return

        providers_snatched = []
        confirmedsnatch = False
        for cs in chk_snatch:
            if cs['Provider'] == 'CBT' or cs['Provider'] == 'KAT':
                logger.info('Invalid provider attached to download (' + cs['Provider'] + '). I cannot find this on 32P, so ignoring this result.')
            elif cs['Status'] == 'Snatched':
                logger.info('Located snatched download:')
                logger.info('--Referencing : ' + cs['Provider'] + ' @ ' + str(cs['DateAdded']))
                providers_snatched.append({'Provider':    cs['Provider'],
                                           'DateAdded':   cs['DateAdded']})
                confirmedsnatch = True
            elif (cs['Status'] == 'Post-Processed' or cs['Status'] == 'Downloaded') and confirmedsnatch == True:
                logger.info('Issue has already been Snatched, Downloaded & Post-Processed.')
                logger.info('You should be using Manual Search or Mark Wanted - not retry the same download.')
                #return

        if len(providers_snatched) == 0:
            return

        chk_logresults = []
        for ps in sorted(providers_snatched, key=itemgetter('DateAdded', 'Provider'), reverse=True):
            try:
                Provider_sql = '%' + ps['Provider'] + '%'
                chk_the_log = myDB.selectone('SELECT * FROM nzblog WHERE IssueID=? AND Provider like (?)', [IssueID, Provider_sql]).fetchone()
            except:
                logger.warn('Unable to locate provider reference for attempted Retry. Will see if I can just get the last attempted download.')
                chk_the_log = myDB.selectone('SELECT * FROM nzblog WHERE IssueID=? and Provider != "CBT" and Provider != "KAT"', [IssueID]).fetchone()

            if chk_the_log is None:
                if len(providers_snatched) == 1:
                    logger.info('Unable to locate provider information ' + ps['Provider'] + ' from nzblog - if you wiped the log, you have to search/download as per normal')
                    return
                else:
                    logger.info('Unable to locate provider information ' + ps['Provider'] + ' from nzblog. Checking additional providers that came back as being used to download this issue')
                    continue
            else:
                chk_logresults.append({'NZBName':   chk_the_log['NZBName'],
                                       'ID':        chk_the_log['ID'],
                                       'PROVIDER':  chk_the_log['PROVIDER']})


        if all([ComicYear is not None, ComicYear != 'None']) and all([IssueID is not None, IssueID != 'None']):
            getYear = myDB.selectone('SELECT IssueDate, ReleaseDate FROM Issues WHERE IssueID=?', [IssueID]).fetchone()
            if getYear is None:
                logger.warn('Unable to retrieve valid Issue Date for Retry of Issue (Try to refresh the series and then try again.')
                return
            if getYear['IssueDate'][:4] == '0000':
                if getYear['ReleaseDate'][:4] == '0000':
                    logger.warn('Unable to retrieve valid Issue Date for Retry of Issue (Try to refresh the series and then try again.')
                    return
                else:
                    ComicYear = getYear['ReleaseDate'][:4]
            else:
                ComicYear = getYear['IssueDate'][:4]

        for chk_log in chk_logresults:
            nzbname = chk_log['NZBName']
            id = chk_log['ID']
            fullprov = chk_log['PROVIDER'] #the full newznab name if it exists will appear here as 'sitename (newznab)'

            #now we break it down by provider to recreate the link.
            #torrents first.
            if any([fullprov == '32P', fullprov == 'TPSE', fullprov == 'WWT', fullprov == 'DEM']):
                if not mylar.ENABLE_TORRENT_SEARCH:
                   logger.error('Torrent Providers are not enabled - unable to process retry request until provider is re-enabled.')
                   continue

                if fullprov == '32P':
                    if not mylar.ENABLE_32P:
                        logger.error('32P is not enabled - unable to process retry request until provider is re-enabled.')
                        continue

                elif any([fullprov == 'TPSE', fullprov == 'WWT', fullprov == 'DEM']):
                    if not mylar.ENABLE_TPSE:
                        logger.error('TPSE is not enabled - unable to process retry request until provider is re-enabled.')
                        continue

                logger.fdebug("sending .torrent to watchdir.")
                logger.fdebug("ComicName:" + ComicName)
                logger.fdebug("Torrent Provider:" + fullprov)
                logger.fdebug("Torrent ID:" + str(id))

                rcheck = mylar.rsscheck.torsend2client(ComicName, IssueNumber, ComicYear, id, fullprov)
                if rcheck == "fail":
                   logger.error("Unable to send torrent - check logs and settings.")
                   continue
                else:
                   logger.info('Successfully retried issue.')
                   break
            else:
                annualize = myDB.selectone('SELECT * FROM annuals WHERE IssueID=?', [IssueID]).fetchone()
                if annualize is None:
                    modcomicname = ComicName
                else:
                    modcomicname = ComicName + ' Annual'

                comicinfo = []
                comicinfo.append({"ComicName":     ComicName,
                                  "IssueNumber":   IssueNumber,
                                  "comyear":       ComicYear,
                                  "modcomicname":  modcomicname})

                newznabinfo = None

                if Provider == 'nzb.su':
                    if not mylar.NZBSU:
                        logger.error('nzb.su is not enabled - unable to process retry request until provider is re-enabled.')
                        continue
                    # http://nzb.su/getnzb/ea1befdeee0affd663735b2b09010140.nzb&i=<uid>&r=<passkey>
                    link = 'http://nzb.su/getnzb/' + str(id) + '.nzb&i=' + str(mylar.NZBSU_UID) + '&r=' + str(mylar.NZBSU_APIKEY)
                    logger.info('fetched via nzb.su. Retrying the send : ' + str(link))
                elif Provider == 'dognzb':
                    if not mylar.DOGNZB:
                        logger.error('Dognzb is not enabled - unable to process retry request until provider is re-enabled.')
                        continue
                    # https://dognzb.cr/fetch/5931874bf7381b274f647712b796f0ac/<passkey>
                    link = 'https://dognzb.cr/fetch/' + str(id) + '/' + str(mylar.DOGNZB_APIKEY)
                    logger.info('fetched via dognzb. Retrying the send : ' + str(link))
                elif Provider == 'experimental':
                    if not mylar.EXPERIMENTAL:
                        logger.error('Experimental is not enabled - unable to process retry request until provider is re-enabled.')
                        continue
                    # http://nzbindex.nl/download/110818178
                    link = 'http://nzbindex.nl/download/' + str(id)
                    logger.info('fetched via experimental. Retrying the send : ' + str(link))
                elif 'newznab' in Provider:
                    if not mylar.NEWZNAB:
                        logger.error('Newznabs are not enabled - unable to process retry request until provider is re-enabled.')
                        continue

                    # http://192.168.2.2/getnzb/4323f9c567c260e3d9fc48e09462946c.nzb&i=<uid>&r=<passkey>
                    # trickier - we have to scroll through all the newznabs until we find a match.
                    logger.info('fetched via newnzab. Retrying the send.')
                    m = re.findall('[^()]+', fullprov)
                    tmpprov = m[0].strip()

                    for newznab_info in mylar.EXTRA_NEWZNABS:
                        if tmpprov.lower() in newznab_info[0].lower():
                            if (newznab_info[5] == '1' or newznab_info[5] == 1):
                                if newznab_info[1].endswith('/'):
                                    newznab_host = newznab_info[1]
                                else:
                                    newznab_host = newznab_info[1] + '/'
                                newznab_api = newznab_info[3]
                                newznab_uid = newznab_info[4]
                                link = str(newznab_host) + 'getnzb/' + str(id) + '.nzb&i=' + str(newznab_uid) + '&r=' + str(newznab_api)
                                logger.info('newznab detected as : ' + str(newznab_info[0]) + ' @ ' + str(newznab_host))
                                logger.info('link : ' + str(link))
                                newznabinfo = (newznab_info[0], newznab_info[1], newznab_info[2], newznab_info[3], newznab_info[4])
                                break
                            else:
                                logger.error(str(newznab_info[0]) + ' is not enabled - unable to process retry request until provider is re-enabled.')
                                continue

                sendit = search.searcher(Provider, nzbname, comicinfo, link=link, IssueID=IssueID, ComicID=ComicID, tmpprov=fullprov, directsend=True, newznab=newznabinfo)
                break
        return
    retryissue.exposed = True

    def queueit(self, **kwargs):
        threading.Thread(target=self.queueissue, kwargs=kwargs).start()
    queueit.exposed = True

    def queueissue(self, mode, ComicName=None, ComicID=None, ComicYear=None, ComicIssue=None, IssueID=None, new=False, redirect=None, SeriesYear=None, SARC=None, IssueArcID=None, manualsearch=None, Publisher=None):
        logger.fdebug('ComicID:' + str(ComicID))
        logger.fdebug('mode:' + str(mode))
        now = datetime.datetime.now()
        myDB = db.DBConnection()
        #mode dictates type of queue - either 'want' for individual comics, or 'series' for series watchlist.
        if ComicID is None and mode == 'series':
            issue = None
            raise cherrypy.HTTPRedirect("searchit?name=%s&issue=%s&mode=%s" % (ComicName, 'None', 'series'))
        elif ComicID is None and mode == 'pullseries':
            # we can limit the search by including the issue # and searching for
            # comics that have X many issues
            raise cherrypy.HTTPRedirect("searchit?name=%s&issue=%s&mode=%s" % (ComicName, 'None', 'pullseries'))
        elif ComicID is None and mode == 'readlist':
            # this is for marking individual comics from a readlist to be downloaded.
            # Because there is no associated ComicID or IssueID, follow same pattern as in 'pullwant'
            # except we know the Year
            if len(ComicYear) > 4:
                ComicYear = ComicYear[:4]
            if SARC is None:
                # it's just a readlist queue (no storyarc mode enabled)
                SARC = True
                IssueArcID = None
            else:
                logger.info(u"Story Arc : " + str(SARC) + " queueing selected issue...")
                logger.info(u"IssueArcID : " + str(IssueArcID))
                #try to load the issue dates - can now sideload issue details.
                dateload = myDB.selectone('SELECT * FROM readinglist WHERE IssueArcID=?', [IssueArcID]).fetchone()
                if dateload is None:
                    IssueDate = None
                    StoreDate = None
                    Publisher = None
                    SeriesYear = None
                else:
                    IssueDate = dateload['IssueDate']
                    StoreDate = dateload['StoreDate']
                    Publisher = dateload['IssuePublisher']
                    SeriesYear = dateload['SeriesYear']

            if ComicYear is None: ComicYear = SeriesYear
            if dateload['Volume'] is None:
                logger.info('Marking ' + ComicName + ' #' + ComicIssue + ' as wanted...')
            else:
                logger.info('Marking ' + ComicName + ' (' + dateload['Volume'] + ') #' + ComicIssue + ' as wanted...')
            logger.fdebug('publisher: ' + Publisher)
            controlValueDict = {"IssueArcID": IssueArcID}
            newStatus = {"Status": "Wanted"}
            myDB.upsert("readinglist", newStatus, controlValueDict)
            foundcom, prov = search.search_init(ComicName=ComicName, IssueNumber=ComicIssue, ComicYear=ComicYear, SeriesYear=None, Publisher=Publisher, IssueDate=IssueDate, StoreDate=StoreDate, IssueID=None, AlternateSearch=None, UseFuzzy=None, ComicVersion=dateload['Volume'], SARC=SARC, IssueArcID=IssueArcID)
            if foundcom  == "yes":
                logger.info(u"Downloaded " + ComicName + " #" + ComicIssue + " (" + str(ComicYear) + ")")
                controlValueDict = {"IssueArcID": IssueArcID}
                newStatus = {"Status": "Snatched"}
            myDB.upsert("readinglist", newStatus, controlValueDict)
            #raise cherrypy.HTTPRedirect("readlist")
            return foundcom

        elif ComicID is None and mode == 'pullwant':
            #this is for marking individual comics from the pullist to be downloaded.
            #because ComicID and IssueID will both be None due to pullist, it's probably
            #better to set both to some generic #, and then filter out later...
            cyear = myDB.selectone("SELECT SHIPDATE FROM weekly").fetchone()
            ComicYear = str(cyear['SHIPDATE'])[:4]
            if Publisher == 'COMICS': Publisher = None
            if ComicYear == '': ComicYear = now.year
            logger.info(u"Marking " + ComicName + " " + ComicIssue + " as wanted...")
            foundcom, prov = search.search_init(ComicName=ComicName, IssueNumber=ComicIssue, ComicYear=ComicYear, SeriesYear=None, Publisher=Publisher, IssueDate=cyear['SHIPDATE'], StoreDate=cyear['SHIPDATE'], IssueID=None, AlternateSearch=None, UseFuzzy=None, ComicVersion=None, allow_packs=False)
            if foundcom  == "yes":
                logger.info(u"Downloaded " + ComicName + " " + ComicIssue)
            raise cherrypy.HTTPRedirect("pullist")
            #return
        elif mode == 'want' or mode == 'want_ann' or manualsearch:
            cdname = myDB.selectone("SELECT * from comics where ComicID=?", [ComicID]).fetchone()
            ComicName_Filesafe = cdname['ComicName_Filesafe']
            SeriesYear = cdname['ComicYear']
            AlternateSearch = cdname['AlternateSearch']
            Publisher = cdname['ComicPublisher']
            UseAFuzzy = cdname['UseFuzzy']
            AllowPacks= cdname['AllowPacks']
            ComicVersion = cdname['ComicVersion']
            ComicName = cdname['ComicName']
            controlValueDict = {"IssueID": IssueID}
            newStatus = {"Status": "Wanted"}
            if mode == 'want':
                if manualsearch:
                    logger.info('Initiating manual search for ' + ComicName + ' issue: ' + ComicIssue)
                else:
                    logger.info(u"Marking " + ComicName + " issue: " + ComicIssue + " as wanted...")
                    myDB.upsert("issues", newStatus, controlValueDict)
            else:
                annual_name = myDB.selectone("SELECT * FROM annuals WHERE ComicID=? and IssueID=?", [ComicID, IssueID]).fetchone()
                if annual_name is None:
                    logger.fdebug('Unable to locate.')
                else:
                    ComicName = annual_name['ReleaseComicName']

                if manualsearch:
                    logger.info('Initiating manual search for ' + ComicName + ' : ' + ComicIssue)
                else:
                    logger.info(u"Marking " + ComicName + " : " + ComicIssue + " as wanted...")
                    myDB.upsert("annuals", newStatus, controlValueDict)
        #---
        #this should be on it's own somewhere
        #if IssueID is not None:
        #    controlValueDict = {"IssueID": IssueID}
        #    newStatus = {"Status": "Wanted"}
        #    myDB.upsert("issues", newStatus, controlValueDict)
        #for future reference, the year should default to current year (.datetime)
        if mode == 'want':
            issues = myDB.selectone("SELECT IssueDate, ReleaseDate FROM issues WHERE IssueID=?", [IssueID]).fetchone()
        elif mode == 'want_ann':
            issues = myDB.selectone("SELECT IssueDate, ReleaseDate FROM annuals WHERE IssueID=?", [IssueID]).fetchone()
        if ComicYear == None:
            ComicYear = str(issues['IssueDate'])[:4]
        if issues['ReleaseDate'] is None or issues['ReleaseDate'] == '0000-00-00':
            logger.info('No Store Date found for given issue. This is probably due to not Refreshing the Series beforehand.')
            logger.info('I Will assume IssueDate as Store Date, but you should probably Refresh the Series and try again if required.')
            storedate = issues['IssueDate']
        else:
            storedate = issues['ReleaseDate']
        #miy = myDB.selectone("SELECT * FROM comics WHERE ComicID=?", [ComicID]).fetchone()
        #SeriesYear = miy['ComicYear']
        #AlternateSearch = miy['AlternateSearch']
        #Publisher = miy['ComicPublisher']
        #UseAFuzzy = miy['UseFuzzy']
        #ComicVersion = miy['ComicVersion']
        foundcom, prov = search.search_init(ComicName, ComicIssue, ComicYear, SeriesYear, Publisher, issues['IssueDate'], storedate, IssueID, AlternateSearch, UseAFuzzy, ComicVersion, mode=mode, ComicID=ComicID, manualsearch=manualsearch, filesafe=ComicName_Filesafe, allow_packs=AllowPacks)
        if foundcom  == "yes":
            # file check to see if issue exists and update 'have' count
            if IssueID is not None:
                logger.info("passing to updater.")
                return updater.foundsearch(ComicID, IssueID, mode=mode, provider=prov)
        if manualsearch:
            # if it's a manual search, return to null here so the thread will die and not cause http redirect errors.
            return
        if ComicID:
            return cherrypy.HTTPRedirect("comicDetails?ComicID=%s" % ComicID)
        else:
            raise cherrypy.HTTPRedirect(redirect)
    queueissue.exposed = True

    def unqueueissue(self, IssueID, ComicID, ComicName=None, Issue=None, FutureID=None, mode=None, ReleaseComicID=None):
        myDB = db.DBConnection()
        if ComicName is None:
            if ReleaseComicID is None:  #ReleaseComicID is used for annuals.
                issue = myDB.selectone('SELECT * FROM issues WHERE IssueID=?', [IssueID]).fetchone()
            else:
                issue = None
            annchk = 'no'
            if issue is None:
                if mylar.ANNUALS_ON:
                    if ReleaseComicID is None:
                        issann = myDB.selectone('SELECT * FROM annuals WHERE IssueID=?', [IssueID]).fetchone()
                    else:
                        issann = myDB.selectone('SELECT * FROM annuals WHERE IssueID=? AND ReleaseComicID=?', [IssueID, ReleaseComicID]).fetchone()
                    ComicName = issann['ReleaseComicName']
                    IssueNumber = issann['Issue_Number']
                    annchk = 'yes'
                    ComicID = issann['ComicID']
                    ReleaseComicID = issann['ReleaseComicID']
            else:
                ComicName = issue['ComicName']
                IssueNumber = issue['Issue_Number']

            controlValueDict = {"IssueID": IssueID}
            if mode == 'failed' and mylar.FAILED_DOWNLOAD_HANDLING:
                logger.info(u"Marking " + ComicName + " issue # " + IssueNumber + " as Failed...")
                newValueDict = {"Status": "Failed"}
                myDB.upsert("failed", newValueDict, controlValueDict)
                if annchk == 'yes':
                   myDB.upsert("annuals", newValueDict, controlValueDict)
                else:
                   myDB.upsert("issues", newValueDict, controlValueDict)
                yield cherrypy.HTTPRedirect("comicDetails?ComicID=%s" % ComicID)
                self.failed_handling(ComicID=ComicID, IssueID=IssueID)
            else:
                logger.info(u"Marking " + ComicName + " issue # " + IssueNumber + " as Skipped...")
                newValueDict = {"Status": "Skipped"}
                if annchk == 'yes':
                   myDB.upsert("annuals", newValueDict, controlValueDict)
                else:
                   myDB.upsert("issues", newValueDict, controlValueDict)
            raise cherrypy.HTTPRedirect("comicDetails?ComicID=%s" % ComicID)
        else:
            #if ComicName is not None, then it's from the FuturePull list that we're 'unwanting' an issue.
            #ComicID may be present if it's a watch from the Watchlist, otherwise it won't exist.
            if ComicID is not None and ComicID != 'None':
                logger.info('comicid present:' + str(ComicID))
                thefuture = myDB.selectone('SELECT * FROM future WHERE ComicID=?', [ComicID]).fetchone()
            else:
                logger.info('FutureID: ' + str(FutureID))
                logger.info('no comicid - ComicName: ' + str(ComicName) + ' -- Issue: #' + Issue)
                thefuture = myDB.selectone('SELECT * FROM future WHERE FutureID=?', [FutureID]).fetchone()
            if thefuture is None:
                logger.info('Cannot find the corresponding issue in the Futures List for some reason. This is probably an Error.')
            else:

                logger.info('Marking ' + thefuture['COMIC'] + ' issue # ' + thefuture['ISSUE']  + ' as skipped...')
                if ComicID is not None and ComicID != 'None':
                    cVDict = {"ComicID": thefuture['ComicID']}
                else:
                    cVDict = {"FutureID": thefuture['FutureID']}
                nVDict = {"Status": "Skipped"}
                logger.info('cVDict:' + str(cVDict))
                logger.info('nVDict:' + str(nVDict))
                myDB.upsert("future", nVDict, cVDict)

    unqueueissue.exposed = True

    def failed_handling(self, ComicID, IssueID):
        import Queue
        queue = Queue.Queue()

        FailProcess = Failed.FailedProcessor(issueid=IssueID, comicid=ComicID, queue=queue)
        thread_ = threading.Thread(target=FailProcess.Process, name="FAILED Post-Processing")
        thread_.start()
        thread_.join()
        failchk = queue.get()
        if failchk[0]['mode'] == 'retry':
            logger.info('Attempting to return to search module with ' + str(failchk[0]['issueid']))
            if failchk[0]['annchk'] == 'no': mode = 'want'
            else: mode = 'want_ann'
            self.queueit(mode=mode, ComicName=failchk[0]['comicname'], ComicIssue=failchk[0]['issuenumber'], ComicID=failchk[0]['comicid'], IssueID=failchk[0]['issueid'], manualsearch=True)
        elif failchk[0]['mode'] == 'stop':
            pass
        else:
            logger.error('mode is unsupported: ' + failchk[0]['mode'])

    failed_handling.exposed = True

    def archiveissue(self, IssueID, comicid):
        myDB = db.DBConnection()
        issue = myDB.selectone('SELECT * FROM issues WHERE IssueID=?', [IssueID]).fetchone()
        annchk = 'no'
        if issue is None:
            if mylar.ANNUALS_ON:
                issann = myDB.selectone('SELECT * FROM annuals WHERE IssueID=?', [IssueID]).fetchone()
                comicname = issann['ReleaseComicName']
                issue = issann['Issue_Number']
                annchk = 'yes'
                comicid = issann['ComicID']
        else:
            comicname = issue['ComicName']
            issue = issue['Issue_Number']
        logger.info(u"Marking " + comicname + " issue # " + str(issue) + " as archived...")
        controlValueDict = {'IssueID': IssueID}
        newValueDict = {'Status': 'Archived'}
        if annchk == 'yes':
            myDB.upsert("annuals", newValueDict, controlValueDict)
        else:
            myDB.upsert("issues", newValueDict, controlValueDict)
        raise cherrypy.HTTPRedirect("comicDetails?ComicID=%s" % comicid)
    archiveissue.exposed = True


    def pullist(self, week=None, year=None):
        myDB = db.DBConnection()
        autowants = myDB.select("SELECT * FROM futureupcoming WHERE Status='Wanted'")
        autowant = []
        if autowants:
            for aw in autowants:
                autowant.append({"ComicName":        aw['ComicName'],
                                 "IssueNumber":      aw['IssueNumber'],
                                 "Publisher":        aw['Publisher'],
                                 "Status":           aw['Status'],
                                 "DisplayComicName": aw['DisplayComicName']})
        weeklyresults = []
        wantedcount = 0

        #find the current week and save it as a reference point.
        todaydate = datetime.datetime.today()
        current_weeknumber = todaydate.strftime("%U")

        if week:
            weeknumber = int(week)
            year = int(year)
            #view specific week (prev_week, next_week)
            startofyear = date(year,1,1)
            week0 = startofyear - timedelta(days=startofyear.isoweekday())
            stweek = datetime.datetime.strptime(week0.strftime('%Y-%m-%d'), '%Y-%m-%d')
            startweek = stweek + timedelta(weeks = weeknumber)
            midweek = startweek + timedelta(days = 3)
            endweek = startweek + timedelta(days = 6)
        else:
            #find the given week number for the current day
            weeknumber = current_weeknumber
            stweek = datetime.datetime.strptime(todaydate.strftime('%Y-%m-%d'), '%Y-%m-%d')
            startweek = stweek - timedelta(days = (stweek.weekday() + 1) % 7)
            midweek = startweek + timedelta(days = 3)
            endweek = startweek + timedelta(days = 6)
            year = todaydate.strftime("%Y")

        prev_week = int(weeknumber) - 1
        next_week = int(weeknumber) + 1

        date_fmt = "%B %d, %Y"

        weekinfo = {'weeknumber':         weeknumber,
                    'startweek':          u"" + startweek.strftime(date_fmt).decode('utf-8'),
                    'midweek':            midweek.strftime('%Y-%m-%d'),
                    'endweek':            u"" + endweek.strftime(date_fmt).decode('utf-8'),
                    'year':               year,
                    'prev_weeknumber':    prev_week,
                    'next_weeknumber':    next_week,
                    'current_weeknumber': current_weeknumber}

        if mylar.WEEKFOLDER_LOC is not None:
            weekdst = mylar.WEEKFOLDER_LOC
        else:
            weekdst = mylar.DESTINATION_DIR

        if mylar.WEEKFOLDER_FORMAT == 0:
            weekfold = os.path.join(weekdst, str( str(weekinfo['year']) + '-' + str(weeknumber) ))
        else:
            weekfold = os.path.join(weekdst, str( str(weekinfo['midweek']) ))

        popit = myDB.select("SELECT * FROM sqlite_master WHERE name='weekly' and type='table'")
        if popit:
            w_results = myDB.select("SELECT * from weekly WHERE weeknumber=?", [str(weeknumber)])
            if len(w_results) == 0:
                logger.info('trying to repopulate to week: ' + str(weeknumber) + '-' + str(year))
                repoll = self.manualpull(weeknumber=weeknumber,year=year)
                if repoll['status'] == 'success':
                    w_results = myDB.select("SELECT * from weekly WHERE weeknumber=?", [str(weeknumber)])
                else:
                    logger.warn('Problem repopulating the pullist for week ' + str(weeknumber) + ', ' + str(year))
                    if mylar.ALT_PULL == 2:
                        logger.warn('Attempting to repoll against legacy pullist in order to have some kind of updated listing for the week.')
                        repoll = self.manualpull()
                        if repoll['status'] == 'success':
                            w_results = myDB.select("SELECT * from weekly WHERE weeknumber=?", [str(weeknumber)])
                        else:
                            logger.warn('Unable to populate the pull-list. Not continuing at this time (will try again in abit)')

            if w_results is None:
                return serve_template(templatename="weeklypull.html", title="Weekly Pull", weeklyresults=weeklyresults, pullfilter=True, weekfold=weekfold, wantedcount=0, weekinfo=weekinfo)

            watchlibrary = helpers.listLibrary()
            issueLibrary = helpers.listIssues(weeknumber, year)

            for weekly in w_results:
                xfound = False
                tmp_status = weekly['Status']
                if weekly['ComicID'] in watchlibrary:
                    haveit = watchlibrary[weekly['ComicID']]

                    if all([week >= weeknumber, mylar.AUTOWANT_UPCOMING, tmp_status == 'Skipped']):
                        tmp_status = 'Wanted'

                    for x in issueLibrary:
                        if weekly['IssueID'] == x['IssueID']:
                            xfound = True
                            tmp_status = x['Status']
                            break

                else:
                    haveit = "No"

                linkit = None
                if all([weekly['ComicID'] is not None, weekly['ComicID'] != '']) and haveit == 'No':
                    linkit = 'http://comicvine.gamespot.com/volume/4050-' + str(weekly['ComicID'])

                x = None
                try:
                    x = float(weekly['ISSUE'])
                except ValueError, e:
                    if 'au' in weekly['ISSUE'].lower() or 'ai' in weekly['ISSUE'].lower() or '.inh' in weekly['ISSUE'].lower() or '.now' in weekly['ISSUE'].lower():
                        x = weekly['ISSUE']

                if x is not None:
                    if not autowant:
                        weeklyresults.append({
                                           "PUBLISHER": weekly['PUBLISHER'],
                                           "ISSUE": weekly['ISSUE'],
                                           "COMIC": weekly['COMIC'],
                                           "STATUS":  tmp_status,
                                           "COMICID": weekly['ComicID'],
                                           "ISSUEID": weekly['IssueID'],
                                           "HAVEIT":  haveit,
                                           "LINK":    linkit,
                                           "AUTOWANT": False
                                         })
                    else:
                        if any(x['ComicName'].lower() == weekly['COMIC'].lower() for x in autowant):
                            weeklyresults.append({
                                           "PUBLISHER": weekly['PUBLISHER'],
                                           "ISSUE": weekly['ISSUE'],
                                           "COMIC": weekly['COMIC'],
                                           "STATUS":  tmp_status,
                                           "COMICID": weekly['ComicID'],
                                           "ISSUEID": weekly['IssueID'],
                                           "HAVEIT":  haveit,
                                           "LINK":    linkit,
                                           "AUTOWANT": True
                                         })
                        else:
                            weeklyresults.append({
                                           "PUBLISHER": weekly['PUBLISHER'],
                                           "ISSUE": weekly['ISSUE'],
                                           "COMIC": weekly['COMIC'],
                                           "STATUS":  tmp_status,
                                           "COMICID": weekly['ComicID'],
                                           "ISSUEID": weekly['IssueID'],
                                           "HAVEIT":  haveit,
                                           "LINK":    linkit,
                                           "AUTOWANT": False
                                         })

                    if tmp_status == 'Wanted':
                        wantedcount +=1

            weeklyresults = sorted(weeklyresults, key=itemgetter('PUBLISHER', 'COMIC'), reverse=False)
        else:
            self.manualpull()

        if week:
            return serve_template(templatename="weeklypull.html", title="Weekly Pull", weeklyresults=weeklyresults, pullfilter=True, weekfold=weekfold, wantedcount=wantedcount, weekinfo=weekinfo)
        else:
            return serve_template(templatename="weeklypull.html", title="Weekly Pull", weeklyresults=weeklyresults, pullfilter=True, weekfold=weekfold, wantedcount=wantedcount, weekinfo=weekinfo)
    pullist.exposed = True

    def removeautowant(self, comicname, release):
        myDB = db.DBConnection()
        logger.fdebug('Removing ' + comicname + ' from the auto-want list.')
        myDB.action("DELETE FROM futureupcoming WHERE ComicName=? AND IssueDate=? AND Status='Wanted'", [comicname, release])
    removeautowant.exposed = True

    def futurepull(self):
        from mylar import solicit
        #get month-year here, and self-populate in future
        now = datetime.datetime.now()
        if len(str(now.month)) != 2:
            month = '0' + str(now.month)
        else:
            month = str(now.month)
        year = str(now.year)
        logger.fdebug('month = ' + str(month))
        logger.fdebug('year = ' + str(year))
        threading.Thread(target=solicit.solicit, args=[month, year]).start()
        raise cherrypy.HTTPRedirect("futurepulllist")
    futurepull.exposed = True

    def futurepulllist(self):
        myDB = db.DBConnection()
        futureresults = []
        watchresults = []
        popthis = myDB.select("SELECT * FROM sqlite_master WHERE name='futureupcoming' and type='table'")
        if popthis:
            l_results = myDB.select("SELECT * FROM futureupcoming WHERE Status='Wanted'")
            for lres in l_results:
                watchresults.append({
                                      "ComicName":   lres['ComicName'],
                                      "IssueNumber": lres['IssueNumber'],
                                      "ComicID":     lres['ComicID'],
                                      "IssueDate":   lres['IssueDate'],
                                      "Publisher":   lres['Publisher'],
                                      "Status":      lres['Status']
                                    })
            logger.fdebug('There are ' + str(len(watchresults)) + ' issues that you are watching for but are not on your watchlist yet.')

        popit = myDB.select("SELECT * FROM sqlite_master WHERE name='future' and type='table'")
        if popit:
            f_results = myDB.select("SELECT SHIPDATE, PUBLISHER, ISSUE, COMIC, EXTRA, STATUS, ComicID, FutureID from future")
            for future in f_results:
                x = None
                if future['ISSUE'] is None: break
                try:
                    x = float(future['ISSUE'])
                except ValueError, e:
                    if 'au' in future['ISSUE'].lower() or 'ai' in future['ISSUE'].lower() or '.inh' in future['ISSUE'].lower() or '.now' in future['ISSUE'].lower():
                        x = future['ISSUE']

                if future['EXTRA'] == 'N/A' or future['EXTRA'] == '':
                    future_extra = ''
                else:
                    future_extra = future['EXTRA']
                    if '(of' in future['EXTRA'].lower():
                        future_extra = re.sub('[\(\)]', '', future['EXTRA'])

                if x is not None:
                    #here we check the status to make sure it's ok since we loaded all the Watch For earlier.
                    chkstatus = future['STATUS']

                    for wr in watchresults:
                        if wr['ComicName'] == future['COMIC'] and wr['IssueNumber'] == future['ISSUE']:
                            logger.info('matched on Name: ' + wr['ComicName'] + ' to ' + future['COMIC'])
                            logger.info('matched on Issue: #' + wr['IssueNumber'] + ' to #' + future['ISSUE'])
                            logger.info('matched on ID: ' + str(wr['ComicID']) + ' to ' + str(future['ComicID']))
                            chkstatus = wr['Status']
                            break

                    futureresults.append({
                                           "SHIPDATE": future['SHIPDATE'],
                                           "PUBLISHER": future['PUBLISHER'],
                                           "ISSUE": future['ISSUE'],
                                           "COMIC": future['COMIC'],
                                           "EXTRA": future_extra,
                                           "STATUS": chkstatus,
                                           "COMICID": future['ComicID'],
                                           "FUTUREID": future['FutureID']
                                         })
            futureresults = sorted(futureresults, key=itemgetter('SHIPDATE', 'PUBLISHER', 'COMIC'), reverse=False)
        else:
            logger.error('No results to post for upcoming issues...something is probably wrong')
            return
        return serve_template(templatename="futurepull.html", title="future Pull", futureresults=futureresults, pullfilter=True)

    futurepulllist.exposed = True

    def add2futurewatchlist(self, ComicName, Issue, Publisher, ShipDate, weeknumber, year, FutureID=None):
        #ShipDate is just weekinfo['midweek'] #a tuple ('weeknumber','startweek','midweek','endweek','year')
        myDB = db.DBConnection()
        logger.info(ShipDate)
        if FutureID is not None:
            chkfuture = myDB.selectone('SELECT * FROM futureupcoming WHERE ComicName=? AND IssueNumber=? WHERE weeknumber=? AND year=?', [ComicName, Issue, weeknumber, year]).fetchone()
            if chkfuture is not None:
                logger.info('Already on Future Upcoming list - not adding at this time.')
                return

        logger.info('Adding ' + ComicName + ' # ' + str(Issue) + ' [' + Publisher + '] to future upcoming watchlist')
        newCtrl = {"ComicName":   ComicName,
                   "IssueNumber": Issue,
                   "Publisher":   Publisher}

        newVal = {"Status":       "Wanted",
                  "IssueDate":    ShipDate,
                  "weeknumber":   weeknumber,
                  "year":         year}

        myDB.upsert("futureupcoming", newVal, newCtrl)

        if FutureID is not None:
            fCtrl = {"FutureID":  FutureID}
            fVal = {"Status":    "Wanted"}
            myDB.upsert("future", fVal, fCtrl)

    add2futurewatchlist.exposed = True

    def future_check(self):
        weeklypull.future_check()
        raise cherrypy.HTTPRedirect("upcoming")
    future_check.exposed = True

    def filterpull(self):
        myDB = db.DBConnection()
        weeklyresults = myDB.select("SELECT * from weekly")
        pulldate = myDB.selectone("SELECT * from weekly").fetchone()
        if pulldate is None:
            if mylar.SAFESTART:
                raise cherrypy.HTTPRedirect("manageComics")
            else:
                raise cherrypy.HTTPRedirect("home")
        return serve_template(templatename="weeklypull.html", title="Weekly Pull", weeklyresults=weeklyresults, pulldate=pulldate['SHIPDATE'], pullfilter=True)
    filterpull.exposed = True

    def manualpull(self,weeknumber=None,year=None):
        logger.info('ALT_PULL: ' + str(mylar.ALT_PULL) + ' PULLBYFILE: ' + str(mylar.PULLBYFILE) + ' week: ' + str(weeknumber) + ' year: ' + str(year))
        if all([mylar.ALT_PULL == 2, mylar.PULLBYFILE is False]) and weeknumber:
            return mylar.locg.locg(weeknumber=weeknumber,year=year)
            #raise cherrypy.HTTPRedirect("pullist?week=" + str(weeknumber) + "&year=" + str(year))
        else:
            weeklypull.pullit()
            return {'status' : 'success'}
    manualpull.exposed = True

    def pullrecreate(self):
        myDB = db.DBConnection()
        myDB.action("DROP TABLE weekly")
        mylar.dbcheck()
        logger.info("Deleted existed pull-list data. Recreating Pull-list...")
        forcecheck = 'yes'
        weeklypull.pullit(forcecheck)
        raise cherrypy.HTTPRedirect("pullist")
    pullrecreate.exposed = True

    def upcoming(self):
        todaydate = datetime.datetime.today()
        current_weeknumber = todaydate.strftime("%U")

        #find the given week number for the current day
        weeknumber = current_weeknumber
        stweek = datetime.datetime.strptime(todaydate.strftime('%Y-%m-%d'), '%Y-%m-%d')
        startweek = stweek - timedelta(days = (stweek.weekday() + 1) % 7)
        midweek = startweek + timedelta(days = 3)
        endweek = startweek + timedelta(days = 6)
        weekyear = todaydate.strftime("%Y")


        myDB = db.DBConnection()
        #upcoming = myDB.select("SELECT * from issues WHERE ReleaseDate > date('now') order by ReleaseDate DESC")
        #upcomingdata = myDB.select("SELECT * from upcoming WHERE IssueID is NULL AND IssueNumber is not NULL AND ComicName is not NULL order by IssueDate DESC")
        #upcomingdata = myDB.select("SELECT * from upcoming WHERE IssueNumber is not NULL AND ComicName is not NULL order by IssueDate DESC")
        upcomingdata = myDB.select("SELECT * from weekly WHERE Issue is not NULL AND Comic is not NULL order by weeknumber DESC")
        if upcomingdata is None:
            logger.info('No upcoming data as of yet...')
        else:
            futureupcoming = []
            upcoming = []
            upcoming_count = 0
            futureupcoming_count = 0
            #try:
            #    pull_date = myDB.selectone("SELECT SHIPDATE from weekly").fetchone()
            #    if (pull_date is None):
            #        pulldate = '00000000'
            #    else:
            #        pulldate = pull_date['SHIPDATE']
            #except (sqlite3.OperationalError, TypeError), msg:
            #    logger.info(u"Error Retrieving weekly pull list - attempting to adjust")
            #    pulldate = '00000000'

            for upc in upcomingdata:
#                if len(upc['IssueDate']) <= 7:
#                    #if it's less than or equal 7, then it's a future-pull so let's check the date and display
#                    #tmpdate = datetime.datetime.com
#                    tmpdatethis = upc['IssueDate']
#                    if tmpdatethis[:2] == '20':
#                        tmpdate = tmpdatethis + '01' #in correct format of yyyymm
#                    else:
#                        findst = tmpdatethis.find('-')  #find the '-'
#                        tmpdate = tmpdatethis[findst +1:] + tmpdatethis[:findst] + '01' #rebuild in format of yyyymm
#                    #timenow = datetime.datetime.now().strftime('%Y%m')
#                else:
#                    #if it's greater than 7 it's a full date.
#                    tmpdate = re.sub("[^0-9]", "", upc['IssueDate'])  #convert date to numerics only (should be in yyyymmdd)

#                timenow = datetime.datetime.now().strftime('%Y%m%d') #convert to yyyymmdd
#                #logger.fdebug('comparing pubdate of: ' + str(tmpdate) + ' to now date of: ' + str(timenow))

#                pulldate = re.sub("[^0-9]", "", pulldate)  #convert pulldate to numerics only (should be in yyyymmdd)

#                if int(tmpdate) >= int(timenow) and int(tmpdate) == int(pulldate): #int(pulldate) <= int(timenow):
                mylar.WANTED_TAB_OFF = False
                try:
                    ab = int(upc['weeknumber'])
                    bc = int(upc['year'])
                except TypeError:
                    logger.warn('Weekly Pull hasn\'t finished being generated as of yet (or has yet to initialize). Try to wait up to a minute to accomodate processing.')
                    mylar.WANTED_TAB_OFF = True
                    myDB.action("DROP TABLE weekly")
                    mylar.dbcheck()
                    logger.info("Deleted existed pull-list data. Recreating Pull-list...")
                    forcecheck = 'yes'
                    return threading.Thread(target=weeklypull.pullit, args=[forcecheck]).start()

                if int(upc['weeknumber']) == int(weeknumber) and int(upc['year']) == int(weekyear):
                    if upc['Status'] == 'Wanted':
                        upcoming_count +=1
                        upcoming.append({"ComicName":    upc['Comic'],
                                         "IssueNumber":  upc['Issue'],
                                         "IssueDate":    upc['ShipDate'],
                                         "ComicID":      upc['ComicID'],
                                         "IssueID":      upc['IssueID'],
                                         "Status":       upc['Status'],
                                         "WeekNumber":   upc['weeknumber'],
                                         "DynamicName":  upc['DynamicName']})

                else:
                    if int(upc['weeknumber']) > int(weeknumber) and upc['Status'] == 'Wanted':
                        futureupcoming_count +=1
                        futureupcoming.append({"ComicName":    upc['Comic'],
                                               "IssueNumber":  upc['Issue'],
                                               "IssueDate":    upc['ShipDate'],
                                               "ComicID":      upc['ComicID'],
                                               "IssueID":      upc['IssueID'],
                                               "Status":       upc['Status'],
                                               "WeekNumber":   upc['weeknumber'],
                                               "DynamicName":  upc['DynamicName']})

#                elif int(tmpdate) >= int(timenow):
#                    if len(upc['IssueDate']) <= 7:
#                        issuedate = tmpdate[:4] + '-' + tmpdate[4:6] + '-00'
#                    else:
#                        issuedate = upc['IssueDate']
#                    if upc['Status'] == 'Wanted':
#                        futureupcoming_count +=1
#                        futureupcoming.append({"ComicName":    upc['ComicName'],
#                                               "IssueNumber":  upc['IssueNumber'],
#                                               "IssueDate":    issuedate,
#                                               "ComicID":      upc['ComicID'],
#                                               "IssueID":      upc['IssueID'],
#                                               "Status":       upc['Status'],
#                                               "DisplayComicName": upc['DisplayComicName']})

        futureupcoming = sorted(futureupcoming, key=itemgetter('IssueDate', 'ComicName', 'IssueNumber'), reverse=True)

        issues = myDB.select("SELECT * from issues WHERE Status='Wanted'")
        if mylar.UPCOMING_SNATCHED:
            issues += myDB.select("SELECT * from issues WHERE Status='Snatched'")
        if mylar.FAILED_DOWNLOAD_HANDLING:
            issues += myDB.select("SELECT * from issues WHERE Status='Failed'")

#       isscnt = myDB.select("SELECT COUNT(*) FROM issues WHERE Status='Wanted' OR Status='Snatched'")
        isCounts = {}
        isCounts[1] = 0   #1 wanted
        isCounts[2] = 0   #2 snatched
        isCounts[3] = 0   #3 failed

        ann_list = []

        ann_cnt = 0

        if mylar.ANNUALS_ON:
            #let's add the annuals to the wanted table so people can see them
            #ComicName wasn't present in db initially - added on startup chk now.
            annuals_list = myDB.select("SELECT * FROM annuals WHERE Status='Wanted'")
            if mylar.UPCOMING_SNATCHED:
                annuals_list += myDB.select("SELECT * FROM annuals WHERE Status='Snatched'")
            if mylar.FAILED_DOWNLOAD_HANDLING:
                annuals_list += myDB.select("SELECT * FROM annuals WHERE Status='Failed'")
#           anncnt = myDB.select("SELECT COUNT(*) FROM annuals WHERE Status='Wanted' OR Status='Snatched'")
#           ann_cnt = anncnt[0][0]
            ann_list += annuals_list
            issues += annuals_list

        for curResult in issues:
            baseissues = {'wanted': 1, 'snatched': 2, 'failed': 3}
            for seas in baseissues:
                if curResult['Status'] is None:
                   continue
                else:
                    if seas in curResult['Status'].lower():
                        sconv = baseissues[seas]
                        isCounts[sconv]+=1
                        continue

        isCounts = {"Wanted": str(isCounts[1]),
                    "Snatched": str(isCounts[2]),
                    "Failed": str(isCounts[3])}

        iss_cnt = int(isCounts['Wanted'])
        wantedcount = iss_cnt# + ann_cnt

        #let's straightload the series that have no issue data associated as of yet (ie. new series) from the futurepulllist
        future_nodata_upcoming = myDB.select("SELECT * FROM futureupcoming WHERE IssueNumber='1' OR IssueNumber='0'")

        #let's move any items from the upcoming table into the wanted table if the date has already passed.
        #gather the list...
        mvupcome = myDB.select("SELECT * from upcoming WHERE IssueDate < date('now') order by IssueDate DESC")
        #get the issue ID's
        for mvup in mvupcome:
            myissue = myDB.selectone("SELECT ComicName, Issue_Number, IssueID, ComicID FROM issues WHERE IssueID=?", [mvup['IssueID']]).fetchone()
            #myissue =  myDB.action("SELECT * FROM issues WHERE Issue_Number=?", [mvup['IssueNumber']]).fetchone()

            if myissue is None: pass
            else:
                logger.fdebug("--Updating Status of issues table because of Upcoming status--")
                logger.fdebug("ComicName: " + str(myissue['ComicName']))
                logger.fdebug("Issue number : " + str(myissue['Issue_Number']))

                mvcontroldict = {"IssueID":    myissue['IssueID']}
                mvvalues = {"ComicID":         myissue['ComicID'],
                            "Status":          "Wanted"}
                myDB.upsert("issues", mvvalues, mvcontroldict)

                #remove old entry from upcoming so it won't try to continually download again.
                logger.fdebug('[DELETE] - ' + mvup['ComicName'] + ' issue #: ' + str(mvup['IssueNumber']))
                deleteit = myDB.action("DELETE from upcoming WHERE ComicName=? AND IssueNumber=?", [mvup['ComicName'], mvup['IssueNumber']])


        return serve_template(templatename="upcoming.html", title="Upcoming", upcoming=upcoming, issues=issues, ann_list=ann_list, futureupcoming=futureupcoming, future_nodata_upcoming=future_nodata_upcoming, futureupcoming_count=futureupcoming_count, upcoming_count=upcoming_count, wantedcount=wantedcount, isCounts=isCounts)
    upcoming.exposed = True

    def skipped2wanted(self, comicid, fromupdate=None):
        # change all issues for a given ComicID that are Skipped, into Wanted.
        issuestowanted = []
        issuesnumwant = []
        myDB = db.DBConnection()
        skipped2 = myDB.select("SELECT * from issues WHERE ComicID=? AND Status='Skipped'", [comicid])
        for skippy in skipped2:
            mvcontroldict = {"IssueID":    skippy['IssueID']}
            mvvalues = {"Status":         "Wanted"}
            myDB.upsert("issues", mvvalues, mvcontroldict)
            issuestowanted.append(skippy['IssueID'])
            issuesnumwant.append(skippy['Issue_Number'])
        if len(issuestowanted) > 0:
            if fromupdate is None:
                logger.info("Marking issues: %s as Wanted" % issuesnumwant)
                threading.Thread(target=search.searchIssueIDList, args=[issuestowanted]).start()
            else:
                logger.info('Marking issues: %s as Wanted' & issuesnumwant)
                logger.info('These will be searched for on next Search Scan / Force Check')
                return
        raise cherrypy.HTTPRedirect("comicDetails?ComicID=%s" % [comicid])
    skipped2wanted.exposed = True

    def annualDelete(self, comicid, ReleaseComicID=None):
        myDB = db.DBConnection()
        if ReleaseComicID is None:
            myDB.action("DELETE FROM annuals WHERE ComicID=?", [comicid])
            logger.fdebug("Deleted all annuals from DB for ComicID of " + str(comicid))
        else:
            myDB.action("DELETE FROM annuals WHERE ReleaseComicID=?", [ReleaseComicID])
            logger.fdebug("Deleted selected annual from DB with a ComicID of " + str(ReleaseComicID))
        raise cherrypy.HTTPRedirect("comicDetails?ComicID=%s" % [comicid])

    annualDelete.exposed = True

    def manualRename(self, comicid):
        if mylar.FILE_FORMAT == '':
            logger.error("You haven't specified a File Format in Configuration/Advanced")
            logger.error("Cannot rename files.")
            return

        myDB = db.DBConnection()
        comic = myDB.selectone("SELECT * FROM comics WHERE ComicID=?", [comicid]).fetchone()
        comicdir = comic['ComicLocation']
        comicname = comic['ComicName']
        extensions = ('.cbr', '.cbz', '.cb7')
        issues = myDB.select("SELECT * FROM issues WHERE ComicID=?", [comicid])
        if mylar.ANNUALS_ON:
            issues += myDB.select("SELECT * FROM annuals WHERE ComicID=?", [comicid])
        comfiles = []
        filefind = 0
        if mylar.MULTIPLE_DEST_DIRS is not None and mylar.MULTIPLE_DEST_DIRS != 'None' and os.path.join(mylar.MULTIPLE_DEST_DIRS, os.path.basename(comicdir)) != comicdir:
            logger.fdebug('multiple_dest_dirs:' + mylar.MULTIPLE_DEST_DIRS)
            logger.fdebug('dir: ' + comicdir)
            logger.fdebug('os.path.basename: ' + os.path.basename(comicdir))
            pathdir = os.path.join(mylar.MULTIPLE_DEST_DIRS, os.path.basename(comicdir))

        for root, dirnames, filenames in os.walk(comicdir):
            for filename in filenames:
                if filename.lower().endswith(extensions):
                    #logger.info("filename being checked is : " + str(filename))
                    for issue in issues:
                        if issue['Location'] == filename:
                            #logger.error("matched " + str(filename) + " to DB file " + str(issue['Location']))
                            if 'annual' in issue['Location'].lower():
                                annualize = 'yes'
                            else:
                                annualize = None
                            renameiss = helpers.rename_param(comicid, comicname, issue['Issue_Number'], filename, comicyear=None, issueid=None, annualize=annualize)
                            nfilename = renameiss['nfilename']
                            srciss = os.path.join(comicdir, filename)
                            if filename != nfilename:
                                logger.info('Renaming ' + filename + ' ... to ... ' + renameiss['nfilename'])
                                try:
                                    shutil.move(srciss, renameiss['destination_dir'])
                                except (OSError, IOError):
                                    logger.error('Failed to move files - check directories and manually re-run.')
                                    return
                                filefind+=1
                            else:
                                logger.info('Not renaming ' + filename + ' as it is in desired format already.')
                            #continue
            logger.info('I have renamed ' + str(filefind) + ' issues of ' + comicname)
            updater.forceRescan(comicid)
    manualRename.exposed = True

    def searchScan(self, name):
        return serve_template(templatename="searchfix.html", title="Manage", name=name)
    searchScan.exposed = True

    def manage(self):
        mylarRoot = mylar.DESTINATION_DIR
        return serve_template(templatename="manage.html", title="Manage", mylarRoot=mylarRoot)
    manage.exposed = True

    def manageComics(self):
        comics = helpers.havetotals()
        return serve_template(templatename="managecomics.html", title="Manage Comics", comics=comics)
    manageComics.exposed = True

    def manageIssues(self, **kwargs):
        status = kwargs['status']
        results = []
        myDB = db.DBConnection()
        if mylar.ANNUALS_ON:
            issues = myDB.select("SELECT * from issues WHERE Status=? AND ComicName NOT LIKE '%Annual%'", [status])
            annuals = myDB.select("SELECT * from annuals WHERE Status=?", [status])
        else:
            issues = myDB.select("SELECT * from issues WHERE Status=?", [status])
            annuals = []
        for iss in issues:
            results.append(iss)
        for ann in annuals:
            results.append(ann)

        return serve_template(templatename="manageissues.html", title="Manage " + str(status) + " Issues", issues=results, status=status)
    manageIssues.exposed = True

    def manageFailed(self):
        results = []
        myDB = db.DBConnection()
        failedlist = myDB.select('SELECT * from Failed')
        for f in failedlist:
            if f['Provider'] == 'TPSE': #if any([f['Provider'] == 'TPSE', f['Provider'] == '32P']):
                link = helpers.torrent_create(f['Provider'], f['ID'])
            else:
                link = f['ID']

            if f['DateFailed'] is None:
                datefailed = '0000-00-0000'
            else:
                datefailed = f['DateFailed']

            results.append({"Series":        f['ComicName'],
                            "ComicID":       f['ComicID'],
                            "Issue_Number":  f['Issue_Number'],
                            "Provider":      f['Provider'],
                            "Link":          link,
                            "ID":            f['ID'],
                            "FileName":      f['NZBName'],
                            "DateFailed":    datefailed})

        return serve_template(templatename="managefailed.html", title="Failed DB Management", failed=results)
    manageFailed.exposed = True

    def manageNew(self):
        myDB = db.DBConnection()
        newcomics = myDB.select('SELECT * from newartists')
        return serve_template(templatename="managenew.html", title="Manage New Artists", newcomics=newcomics)
    manageNew.exposed = True

    def flushImports(self):
        myDB = db.DBConnection()
        myDB.action('DELETE from importresults')
        logger.info("Flushing all Import Results and clearing the tables")
    flushImports.exposed = True

    def markImports(self, action=None, **args):
        myDB = db.DBConnection()
        comicstoimport = []
        if action == 'massimport':
            logger.info('Initiating mass import.')
            cnames = myDB.select("SELECT ComicName, ComicID, Volume, DynamicName from importresults WHERE Status='Not Imported' GROUP BY DynamicName, Volume")
            for cname in cnames:
                if cname['ComicID']:
                    comicid = cname['ComicID']
                else:
                    comicid = None
                comicstoimport.append({'ComicName':   cname['ComicName'].decode('utf-8', 'replace'),
                                       'DynamicName': cname['DynamicName'],
                                       'Volume':      cname['Volume'],
                                       'ComicID':     comicid})
            logger.info(str(len(comicstoimport)) + ' series will be attempted to be imported.')
        else:
            if action == 'importselected':
                logger.info('importing selected series.')
                for k,v in args.items():
                    #k = Comicname[Volume]
                    #v = DynamicName
                    Volst = k.find('[')
                    volume = re.sub('[\[\]]', '', k[Volst:]).strip()
                    ComicName = k[:Volst].strip()
                    DynamicName = v
                    cid = ComicName.decode('utf-8', 'replace')
                    comicstoimport.append({'ComicName': cid,
                                           'DynamicName': DynamicName,
                                           'Volume':    volume,
                                           'ComicID':   None})

            elif action == 'removeimport':
                for k,v in args.items():
                    Volst = k.find('[')
                    volume = re.sub('[\[\]]', '', k[Volst:]).strip()
                    ComicName = k[:Volst].strip()
                    DynamicName = v
                    if volume is None or volume == 'None':
                        logger.info('Removing ' + ComicName + ' from the Import list')
                        myDB.action('DELETE from importresults WHERE DynamicName=? AND (Volume is NULL OR Volume="None")', [DynamicName])
                    else:
                        logger.info('Removing ' + ComicName + ' [' + str(volume) + '] from the Import list')
                        myDB.action('DELETE from importresults WHERE DynamicName=? AND Volume=?', [DynamicName, volume])

            if len(comicstoimport) > 0:
                logger.info('Initiating selected import mode for ' + str(len(comicstoimport)) + ' series.')

        if len(comicstoimport) > 0:
            logger.debug('The following series will now be attempted to be imported: %s' % comicstoimport)
            threading.Thread(target=self.preSearchit, args=[None, comicstoimport, len(comicstoimport)]).start()
        raise cherrypy.HTTPRedirect("importResults")

    markImports.exposed = True

    def markComics(self, action=None, **args):
        myDB = db.DBConnection()
        comicsToAdd = []
        for k,v in args.items():
            if k == 'manage_comic_length':
                continue
            #k = Comicname[ComicYear]
            #v = ComicID
            comyr = k.find('[')
            ComicYear = re.sub('[\[\]]', '', k[comyr:]).strip()
            ComicName = k[:comyr].strip()
            ComicID = v
            #cid = ComicName.decode('utf-8', 'replace')

            if action == 'delete':
                logger.info('[MANAGE COMICS][DELETION] Now deleting ' + ComicName + ' (' + str(ComicYear) + ') [' + str(ComicID) + '] form the DB.')
                myDB.action('DELETE from comics WHERE ComicID=?', [ComicID])
                myDB.action('DELETE from issues WHERE ComicID=?', [ComicID])
                logger.info('[MANAGE COMICS][DELETION] Successfully deleted ' + ComicName + '(' + str(ComicYear) + ')')
            elif action == 'pause':
                controlValueDict = {'ComicID': ComicID}
                newValueDict = {'Status': 'Paused'}
                myDB.upsert("comics", newValueDict, controlValueDict)
                logger.info('[MANAGE COMICS][PAUSE] ' + ComicName + ' has now been put into a Paused State.')
            elif action == 'resume':
                controlValueDict = {'ComicID': ComicID}
                newValueDict = {'Status': 'Active'}
                myDB.upsert("comics", newValueDict, controlValueDict)
                logger.info('[MANAGE COMICS][RESUME] ' + ComicName + ' has now been put into a Resumed State.')
            elif action == 'recheck' or action == 'metatag':
                comicsToAdd.append({'ComicID':   ComicID,
                                    'ComicName': ComicName,
                                    'ComicYear': ComicYear})
            else:
                comicsToAdd.append(ComicID)

        if len(comicsToAdd) > 0:
            if action == 'recheck':
                logger.info('[MANAGE COMICS][RECHECK-FILES] Rechecking Files for  ' + str(len(comicsToAdd)) + ' series')
                threading.Thread(target=self.forceRescan, args=[comicsToAdd,True,'recheck']).start()
            elif action == 'metatag':
                logger.info('[MANAGE COMICS][MASS METATAGGING] Now Metatagging Files for  ' + str(len(comicsToAdd)) + ' series')
                threading.Thread(target=self.forceRescan, args=[comicsToAdd,True,'metatag']).start()
            else:
                logger.info('[MANAGE COMICS][REFRESH] Refreshing ' + str(len(comicsToAdd)) + ' series')
                threading.Thread(target=updater.dbUpdate, args=[comicsToAdd]).start()
    markComics.exposed = True

    def forceUpdate(self):
        from mylar import updater
        threading.Thread(target=updater.dbUpdate).start()
        raise cherrypy.HTTPRedirect("home")
    forceUpdate.exposed = True

    def forceSearch(self):
        from mylar import search
        threading.Thread(target=search.searchforissue).start()
        raise cherrypy.HTTPRedirect("home")
    forceSearch.exposed = True

    def forceRescan(self, ComicID, bulk=False, action='recheck'):
        if bulk:
            cnt = 1
            if action == 'recheck':
                for cid in ComicID:
                    logger.info('[MASS BATCH][RECHECK-FILES][' + str(cnt) + '/' + str(len(ComicID)) + '] Rechecking ' + cid['ComicName'] + '(' + str(cid['ComicYear']) + ')')
                    updater.forceRescan(cid['ComicID'])
                    cnt+=1
                logger.info('[MASS BATCH][RECHECK-FILES] I have completed rechecking files for ' + str(len(ComicID)) + ' series.')
            else:
                for cid in ComicID:
                    logger.info('[MASS BATCH][METATAGGING-FILES][' + str(cnt) + '/' + str(len(ComicID)) + '] Now Preparing to metatag series for ' + cid['ComicName'] + '(' + str(cid['ComicYear']) + ')')
                    self.group_metatag(ComicID=cid['ComicID'])
                    cnt+=1
                logger.info('[MASS BATCH][METATAGGING-FILES] I have completed metatagging files for ' + str(len(ComicID)) + ' series.')

        else:
            threading.Thread(target=updater.forceRescan, args=[ComicID]).start()
    forceRescan.exposed = True

    def checkGithub(self):
        from mylar import versioncheck
        versioncheck.checkGithub()
        if mylar.SAFESTART:
            raise cherrypy.HTTPRedirect("manageComics")
        else:
            raise cherrypy.HTTPRedirect("home")
    checkGithub.exposed = True

    def history(self):
        myDB = db.DBConnection()
        history = myDB.select('''SELECT * from snatched order by DateAdded DESC''')
        return serve_template(templatename="history.html", title="History", history=history)
    history.exposed = True

    def reOrder(request):
        return request
#        return serve_template(templatename="reorder.html", title="ReoRdered!", reorder=request)
    reOrder.exposed = True

    def readlist(self):
        myDB = db.DBConnection()
        issuelist = myDB.select("SELECT * from readlist")
        #tuple this
        readlist = []
        counts = []
        c_added = 0  #count of issues that have been added to the readlist and remain in that status ( meaning not sent / read )
        c_sent = 0   #count of issues that have been sent to a third-party device ( auto-marked after a successful send completion )
        c_read = 0   #count of issues that have been marked as read ( manually marked as read - future: read state from xml )
        for iss in issuelist:
            if iss['Status'] == 'Added':
                statuschange = iss['DateAdded']
                c_added +=1
            else:
                if iss['Status'] == 'Read':
                    c_read +=1
                elif iss['Status'] == 'Downloaded':
                    c_sent +=1
                statuschange = iss['StatusChange']

            readlist.append({"ComicID":       iss['ComicID'],
                             "ComicName":     iss['ComicName'],
                             "SeriesYear":    iss['SeriesYear'],
                             "Issue_Number":  iss['Issue_Number'],
                             "IssueDate":     iss['IssueDate'],
                             "Status":        iss['Status'],
                             "StatusChange":  statuschange,
                             "inCacheDIR":    iss['inCacheDIR'],
                             "Location":      iss['Location'],
                             "IssueID":       iss['IssueID']})

        counts = {"added": c_added,
                   "read":  c_read,
                   "sent":  c_sent,
                   "total": (c_added + c_read + c_sent)}

        return serve_template(templatename="readinglist.html", title="Reading Lists", issuelist=readlist, counts=counts)
    readlist.exposed = True

    def storyarc_main(self):
        myDB = db.DBConnection()
        arclist = []
        alist = myDB.select("SELECT * from readinglist WHERE ComicName is not Null group by StoryArcID") #COLLATE NOCASE")
        for al in alist:
            totalissues = myDB.select("SELECT COUNT(*) as count from readinglist WHERE StoryARcID=?", [al['StoryArcID']])

            havecnt = myDB.select("SELECT COUNT(*) as count FROM readinglist WHERE StoryArcID=? AND (Status='Downloaded' or Status='Archived')", [al['StoryArcID']])
            havearc = havecnt[0][0]
            totalarc = totalissues[0][0]
            if not havearc:
                 havearc = 0
            try:
                 percent = (havearc *100.0) /totalarc
                 if percent > 100:
                     percent = 101
            except (ZeroDivisionError, TypeError):
                 percent = 0
                 totalarc = '?'


            arclist.append({"StoryArcID":       al['StoryArcID'],
                            "StoryArc":         al['StoryArc'],
                            "TotalIssues":      al['TotalIssues'],
                            "SeriesYear":       al['SeriesYear'],
                            "StoryArcDir":      al['StoryArc'],
                            "Status":           al['Status'],
                            "percent":          percent,
                            "Have":             havearc,
                            "SpanYears":        helpers.spantheyears(al['StoryArcID']),
                            "Total":            totalarc,
                            "CV_ArcID":         al['CV_ArcID']})
        return serve_template(templatename="storyarc.html", title="Story Arcs", arclist=arclist, delete_type=0)
    storyarc_main.exposed = True

    def detailStoryArc(self, StoryArcID, StoryArcName):
        myDB = db.DBConnection()
        arcinfo = myDB.select("SELECT * from readinglist WHERE StoryArcID=? order by ReadingOrder ASC", [StoryArcID])
        try:
            cvarcid = arcinfo[0]['CV_ArcID']
            arcpub = arcinfo[0]['Publisher']
            lowyear = 9999
            maxyear = 0
            issref = []
            for la in arcinfo:
                if all([la['Status'] == 'Downloaded', la['Location'] is None,]):
                    issref.append({'IssueID':         la['IssueID'],
                                   'ComicID':         la['ComicID'],
                                   'IssuePublisher':  la['IssuePublisher'],
                                   'Publisher':       la['Publisher'],
                                   'StoryArc':        la['StoryArc'],
                                   'StoryArcID':      la['StoryArcID'],
                                   'ComicName':       la['ComicName'],
                                   'IssueNumber':     la['IssueNumber'],
                                   'ReadingOrder':    la['ReadingOrder']})

                if la['IssueDate'] is None:
                    continue
                else:
                    if int(la['IssueDate'][:4]) > maxyear:
                        maxyear = int(la['IssueDate'][:4])
                    if int(la['IssueDate'][:4]) < lowyear:
                        lowyear = int(la['IssueDate'][:4])
                                   

            if maxyear == 0:
                spanyears = la['SeriesYear']
            elif lowyear == maxyear:
                spanyears = str(maxyear)
            else:
                spanyears = str(lowyear) + ' - ' + str(maxyear)

            sdir = helpers.arcformat(arcinfo[0]['StoryArc'], spanyears, arcpub)

        except:
            cvarcid = None
            sdir = mylar.GRABBAG_DIR

        if len(issref) > 0:
            logger.info(issref)
            helpers.updatearc_locs(StoryArcID, issref)
            arcinfo = myDB.select("SELECT * from readinglist WHERE StoryArcID=? order by ReadingOrder ASC", [StoryArcID])

        return serve_template(templatename="storyarc_detail.html", title="Detailed Arc list", readlist=arcinfo, storyarcname=StoryArcName, storyarcid=StoryArcID, cvarcid=cvarcid, sdir=sdir)
    detailStoryArc.exposed = True

    def markreads(self, action=None, **args):
        sendtablet_queue = []
        myDB = db.DBConnection()
        for IssueID in args:
            if IssueID is None or 'issue_table' in IssueID or 'issue_table_length' in IssueID:
                continue
            else:
                mi = myDB.selectone("SELECT * FROM readlist WHERE IssueID=?", [IssueID]).fetchone()
                if mi is None:
                    continue
                else:
                    comicname = mi['ComicName']

                if action == 'Downloaded':
                    logger.fdebug(u"Marking %s #%s as %s" % (comicname, mi['Issue_Number'], action))
                    read = readinglist.Readinglist(IssueID)
                    read.addtoreadlist()
                elif action == 'Read':
                    logger.fdebug(u"Marking %s #%s as %s" % (comicname, mi['Issue_Number'], action))
                    markasRead(IssueID)
                elif action == 'Added':
                    logger.fdebug(u"Marking %s #%s as %s" % (comicname, mi['Issue_Number'], action))
                    read = readinglist.Readinglist(IssueID=IssueID)
                    read.addtoreadlist()
                elif action == 'Remove':
                    logger.fdebug('Deleting %s #%s' % (comicname, mi['Issue_Number']))
                    myDB.action('DELETE from readlist WHERE IssueID=?', [IssueID])
                elif action == 'Send':
                    logger.fdebug('Queuing ' + mi['Location'] + ' to send to tablet.')
                    sendtablet_queue.append({"filepath": mi['Location'],
                                             "issueid":  IssueID,
                                             "comicid":  mi['ComicID']})
        if len(sendtablet_queue) > 0:
            read = readinglist.Readinglist(sendtablet_queue)
            threading.Thread(target=read.syncreading).start()

    markreads.exposed = True

    def removefromreadlist(self, IssueID=None, StoryArcID=None, IssueArcID=None, AllRead=None, ArcName=None, delete_type=None):
        myDB = db.DBConnection()
        if IssueID:
            myDB.action('DELETE from readlist WHERE IssueID=?', [IssueID])
            logger.info("[DELETE-READ-ISSUE] Removed " + str(IssueID) + " from Reading List")
        elif StoryArcID:
            logger.info('[DELETE-ARC] Removing ' + ArcName + ' from your Story Arc Watchlist')
            myDB.action('DELETE from readinglist WHERE StoryArcID=?', [StoryArcID])
            #ArcName should be an optional flag so that it doesn't remove arcs that have identical naming (ie. Secret Wars)
            if delete_type:
                if ArcName:
                    logger.info('[DELETE-STRAGGLERS-OPTION] Removing all traces of arcs with the name of : ' + ArcName)
                    myDB.action('DELETE from readinglist WHERE StoryArc=?', [ArcName])
                else:
                    logger.warn('[DELETE-STRAGGLERS-OPTION] No ArcName provided - just deleting by Story Arc ID')
            stid = 'S' + str(StoryArcID) + '_%'
            #delete from the nzblog so it will always find the most current downloads. Nzblog has issueid, but starts with ArcID
            myDB.action('DELETE from nzblog WHERE IssueID LIKE ?', [stid])
            logger.info("[DELETE-ARC] Removed " + str(StoryArcID) + " from Story Arcs.")
        elif IssueArcID:
            myDB.action('DELETE from readinglist WHERE IssueArcID=?', [IssueArcID])
            logger.info("[DELETE-ARC] Removed " + str(IssueArcID) + " from the Story Arc.")
        elif AllRead:
            myDB.action("DELETE from readlist WHERE Status='Read'")
            logger.info("[DELETE-ALL-READ] Removed All issues that have been marked as Read from Reading List")
    removefromreadlist.exposed = True

    def markasRead(self, IssueID=None, IssueArcID=None):
        read = readinglist.Readinglist(IssueID, IssueArcID)
        read.markasRead()
    markasRead.exposed = True

    def addtoreadlist(self, IssueID):
        read = readinglist.Readinglist(IssueID=IssueID)
        read.addtoreadlist()
        return
        #raise cherrypy.HTTPRedirect("comicDetails?ComicID=%s" % readlist['ComicID'])
    addtoreadlist.exposed = True

    def importReadlist(self, filename):
        from xml.dom.minidom import parseString, Element
        import random
        myDB = db.DBConnection()

        file = open(filename)
        data = file.read()
        file.close()

        dom = parseString(data)
        # of results
        storyarc = dom.getElementsByTagName('Name')[0].firstChild.wholeText
        tracks = dom.getElementsByTagName('Book')
        i = 1
        node = dom.documentElement
        logger.fdebug("there are " + str(len(tracks)) + " issues in the story-arc: " + str(storyarc))
        #generate a random number for the ID, and tack on the total issue count to the end as a str :)
        storyarcid = str(random.randint(1000, 9999)) + str(len(tracks))
        i = 1
        for book_element in tracks:
            st_issueid = str(storyarcid) + "_" + str(random.randint(1000, 9999))
            comicname = book_element.getAttribute('Series')
            logger.fdebug("comic: " + comicname)
            comicnumber = book_element.getAttribute('Number')
            logger.fdebug("number: " + str(comicnumber))
            comicvolume = book_element.getAttribute('Volume')
            logger.fdebug("volume: " + str(comicvolume))
            comicyear = book_element.getAttribute('Year')
            logger.fdebug("year: " + str(comicyear))
            CtrlVal = {"IssueArcID": st_issueid}
            NewVals = {"StoryArcID":  storyarcid,
                       "ComicName":   comicname,
                       "IssueNumber": comicnumber,
                       "SeriesYear":  comicvolume,
                       "IssueYear":   comicyear,
                       "StoryArc":    storyarc,
                       "ReadingOrder": i,
                       "TotalIssues": len(tracks)}
            myDB.upsert("readinglist", NewVals, CtrlVal)
            i+=1

        # Now we either load in all of the issue data for series' already on the watchlist,
        # or we dynamically load them from CV and write to the db.

        #this loads in all the series' that have multiple entries in the current story arc.
        Arc_MultipleSeries = myDB.select("SELECT * FROM readinglist WHERE StoryArcID=? AND IssueID is NULL GROUP BY ComicName HAVING (COUNT(ComicName) > 1)", [storyarcid])

        if Arc_MultipleSeries is None:
            logger.info('Detected 0 series that have multiple entries in this Story Arc. Continuing.')

        else:
            AMS = []
            for Arc_MS in Arc_MultipleSeries:
                print Arc_MS
                #the purpose of this loop is to loop through the multiple entries, pulling out the lowest & highest issue numbers
                #along with the publication years in order to help the auto-detector attempt to figure out what the series is on CV.
                #.schema readinglist
                #(StoryArcID TEXT, ComicName TEXT, IssueNumber TEXT, SeriesYear TEXT, IssueYEAR TEXT, StoryArc TEXT, TotalIssues TEXT,
                # Status TEXT, inCacheDir TEXT, Location TEXT, IssueArcID TEXT, ReadingOrder INT, IssueID TEXT);
                AMS.append({"StoryArcID":  Arc_MS['StoryArcID'],
                            "ComicName":   Arc_MS['ComicName'],
                            "SeriesYear":  Arc_MS['SeriesYear'],
                            "IssueYear":   Arc_MS['IssueYear'],
                            "IssueID":     Arc_MS['IssueID'],
                            "highvalue":   '0',
                            "lowvalue":    '9999',
                            "yearRANGE":   [str(Arc_MS['SeriesYear'])]}) #Arc_MS['SeriesYear']})

            for MSCheck in AMS:
                thischk = myDB.select('SELECT * FROM readinglist WHERE ComicName=? AND SeriesYear=?', [MSCheck['ComicName'], MSCheck['SeriesYear']])
                for tchk in thischk:
                    if helpers.issuedigits(tchk['IssueNumber']) > helpers.issuedigits(MSCheck['highvalue']):
                        for key in MSCheck.keys():
                            if key == "highvalue":
                                MSCheck[key] = tchk['IssueNumber']

                    if helpers.issuedigits(tchk['IssueNumber']) < helpers.issuedigits(MSCheck['lowvalue']):
                        for key in MSCheck.keys():
                            if key == "lowvalue":
                                MSCheck[key] = tchk['IssueNumber']

                    logger.fdebug(str(tchk['IssueYear']))
                    logger.fdebug(MSCheck['yearRANGE'])
                    if str(tchk['IssueYear']) not in str(MSCheck['yearRANGE']):
                        for key in MSCheck.keys():
                            if key == "yearRANGE":
                                MSCheck[key].append(str(tchk['IssueYear']))

                #write out here
                #logger.fdebug(str(MSCheck))

        #now we load in the list without the multiple entries (ie. series that appear only once in the cbl and don't have an IssueID)
        Arc_Issues = myDB.select("SELECT * FROM readinglist WHERE StoryArcID=? AND IssueID is NULL GROUP BY ComicName HAVING (COUNT(ComicName) = 1)", [storyarcid])
        if Arc_Issues is None:
            logger.fdebug('No individual series detected within the Reading list (series that only appear once).')
        else:
            logger.fdebug('Detected series that occur only once in the Reading List.')
            for AI in Arc_Issues:
                logger.fdebug('Detected ' + AI['ComicName'] + ' (' + AI['SeriesYear'] + ') #' + AI['IssueNumber'])
                AMS.append({"StoryArcID":  AI['StoryArcID'],
                            "ComicName":   AI['ComicName'],
                            "SeriesYear":  AI['SeriesYear'],
                            "IssueYear":   AI['IssueYear'],
                            "IssueID":     AI['IssueID'],
                            "highvalue":   AI['IssueNumber'],
                            "lowvalue":    AI['IssueNumber'],
                            "yearRANGE":   AI['IssueYear']})

        logger.fdebug('AMS:' + str(AMS))
        logger.fdebug('I need to now try to populate ' + str(len(AMS)) + ' series.')

        Arc_Data = []

        for duh in AMS:
            mode='series'
            sresults, explicit = mb.findComic(duh['ComicName'], mode, issue=duh['highvalue'], limityear=duh['yearRANGE'], explicit='all')
            type='comic'

            if len(sresults) == 1:
                sr = sresults[0]
                logger.info('Only one result...automagik-mode enabled for ' + duh['ComicName'] + ' :: ' + str(sr['comicid']) + ' :: Publisher : ' + str(sr['publisher']))
                issues = mylar.cv.getComic(sr['comicid'], 'issue')
                isscnt = len(issues['issuechoice'])
                logger.info('isscnt : ' + str(isscnt))
                chklist = myDB.select('SELECT * FROM readinglist WHERE StoryArcID=? AND ComicName=? AND SeriesYear=?', [duh['StoryArcID'], duh['ComicName'], duh['SeriesYear']])
                if chklist is None:
                    logger.error('I did not find anything in the Story Arc. Something is probably wrong.')
                    continue
                else:
                    n = 0
                    while (n <= isscnt):
                        try:
                            islval = issues['issuechoice'][n]
                        except IndexError:
                            break

                        for d in chklist:
                            if islval['Issue_Number'] == d['IssueNumber']:
                                logger.info('[' + str(islval['Issue_ID']) + '] matched on Issue Number for ' + duh['ComicName'] + ' #' + str(d['IssueNumber']))
                                logger.info('I should write these dates: ' + islval['Issue_Date'] + ' -- ' + islval['Store_Date'])
                                Arc_Data.append({"StoryArcID":    duh['StoryArcID'],
                                                 "IssueArcID":    d['IssueArcID'],
                                                 "ComicID":       islval['Comic_ID'],
                                                 "IssueID":       islval['Issue_ID'],
                                                 "Issue_Number":  islval['Issue_Number'],
                                                 "Issue_Date":    islval['Issue_Date'],
                                                 "Publisher":     sr['publisher'],
                                                 "Store_Date":    islval['Store_Date']})
                                break
                        n+=1
                #the below cresults will auto-add and cycle through until all are added to watchlist
                #cresults = importer.addComictoDB(sr['comicid'],"no",None)

            else:
                logger.fdebug('Returning results to screen - more than one possibility.')
                resultset = 0

        logger.info('I need to update ' + str(len(Arc_Data)) + ' issues in this Reading List with CV Issue Data.')
        if len(Arc_Data) > 0:
            for AD in Arc_Data:
                newCtrl = {"IssueArcID":  AD['IssueArcID']}
                newVals = {"ComicID":     AD['ComicID'],
                           "IssueID":     AD['IssueID'],
                           "Publisher":   AD['Publisher'],
                           "IssueDate":   AD['Issue_Date'],
                           "StoreDate":   AD['Store_Date']}

                logger.info('CTRLWRITE TO: ' + str(newCtrl))
                logger.info('WRITING: ' + str(newVals))

                myDB.upsert("readinglist", newVals, newCtrl)


        raise cherrypy.HTTPRedirect("detailStoryArc?StoryArcID=%s&StoryArcName=%s" % (storyarcid, storyarc))
    importReadlist.exposed = True

    def ArcWatchlist(self,StoryArcID=None):
        myDB = db.DBConnection()
        if StoryArcID:
            ArcWatch = myDB.select("SELECT * FROM readinglist WHERE StoryArcID=?", [StoryArcID])
        else:
            ArcWatch = myDB.select("SELECT * FROM readinglist")

        if ArcWatch is None:
            logger.info("No Story Arcs to search")
        else:
            #cycle through the story arcs here for matches on the watchlist
            arcdir = helpers.filesafe(ArcWatch[0]['StoryArc'])
            arcpub = ArcWatch[0]['Publisher']
            if arcpub is None:
                arcpub = ArcWatch[0]['IssuePublisher']
            lowyear = 9999
            maxyear = 0
            for la in ArcWatch:
                if la['IssueDate'] is None:
                    continue
                else:
                    if int(la['IssueDate'][:4]) > maxyear:
                        maxyear = int(la['IssueDate'][:4])
                    if int(la['IssueDate'][:4]) < lowyear:
                        lowyear = int(la['IssueDate'][:4])

            if maxyear == 0:
                spanyears = la['SeriesYear']
            elif lowyear == maxyear:
                spanyears = str(maxyear)
            else:
                spanyears = str(lowyear) + ' - ' + str(maxyear)

            logger.info('arcpub: ' + arcpub)
            dstloc = helpers.arcformat(arcdir, spanyears, arcpub)

            #if not os.path.isdir(dstloc) and mylar.STORYARCDIR:
            #    logger.info('Story Arc Directory [' + dstloc + '] does not exist! - attempting to create now.')
            #    checkdirectory = filechecker.validateAndCreateDirectory(dstloc, True)
            #    if not checkdirectory:
            #        logger.warn('Error trying to validate/create directory. Aborting this process at this time.')
            #        return

            if all([mylar.CVINFO, mylar.STORYARCDIR]):
                if not os.path.isfile(os.path.join(dstloc, "cvinfo")) or mylar.CV_ONETIMER:
                    logger.fdebug('Generating cvinfo file for story-arc.')
                    with open(os.path.join(dstloc, "cvinfo"), "w") as text_file:
                        if any([ArcWatch[0]['StoryArcID'] == ArcWatch[0]['CV_ArcID'], ArcWatch[0]['CV_ArcID'] is None]):
                            cvinfo_arcid = ArcWatch[0]['StoryArcID']
                        else:
                            cvinfo_arcid = ArcWatch[0]['CV_ArcID']

                        text_file.write('https://comicvine.gamespot.com/storyarc/4045-' + str(cvinfo_arcid))
                    if mylar.ENFORCE_PERMS:
                        filechecker.setperms(os.path.join(dstloc, 'cvinfo'))

            #get the list of files within the storyarc directory, if any.
            filelist = None
            if mylar.STORYARCDIR:
                fchk = filechecker.FileChecker(dir=dstloc, watchcomic=None, Publisher=None, sarc='true', justparse=True)
                filechk = fchk.listFiles()
                fccnt = filechk['comiccount']
                logger.fdebug('[STORY ARC DIRECTORY] ' + str(fccnt) + ' files exist within this directory.')
                if fccnt > 0:
                    filelist = filechk['comiclist']
                logger.info(filechk)

            arc_match = []
            wantedlist = []

            sarc_title = None
            showonreadlist = 1 # 0 won't show storyarcissues on readinglist main page, 1 will show
            for arc in ArcWatch:
                sarc_title = arc['StoryArc']
                logger.fdebug('[' + arc['StoryArc'] + '] ' + arc['ComicName'] + ' : ' + arc['IssueNumber'])

                matcheroso = "no"
                #fc = filechecker.FileChecker(watchcomic=arc['ComicName'])
                #modi_names = fc.dynamic_replace(arc['ComicName'])
                #mod_arc = re.sub('[\|\s]', '', modi_names['mod_watchcomic'].lower()).strip()   #is from the arc db

                comics = myDB.select("SELECT * FROM comics WHERE DynamicComicName IN (?) COLLATE NOCASE", [arc['DynamicComicName']])

                for comic in comics:
                    mod_watch = comic['DynamicComicName'] #is from the comics db

                    if re.sub('[\|\s]','', mod_watch.lower()).strip() == re.sub('[\|\s]', '', arc['DynamicComicName'].lower()).strip():
                        logger.fdebug("initial name match - confirming issue # is present in series")
                        if comic['ComicID'][:1] == 'G':
                            # if it's a multi-volume series, it's decimalized - let's get rid of the decimal.
                            GCDissue, whocares = helpers.decimal_issue(arc['IssueNumber'])
                            GCDissue = int(GCDissue) / 1000
                            if '.' not in str(GCDissue): GCDissue = str(GCDissue) + ".00"
                            logger.fdebug("issue converted to " + str(GCDissue))
                            isschk = myDB.selectone("SELECT * FROM issues WHERE Issue_Number=? AND ComicID=?", [str(GCDissue), comic['ComicID']]).fetchone()
                        else:
                            issue_int = helpers.issuedigits(arc['IssueNumber'])
                            logger.fdebug('int_issue = ' + str(issue_int))
                            isschk = myDB.selectone("SELECT * FROM issues WHERE Int_IssueNumber=? AND ComicID=?", [issue_int, comic['ComicID']]).fetchone() #AND STATUS !='Snatched'", [issue_int, comic['ComicID']]).fetchone()
                        if isschk is None:
                            logger.fdebug("we matched on name, but issue " + arc['IssueNumber'] + " doesn't exist for " + comic['ComicName'])
                        else:
                            #this gets ugly - if the name matches and the issue, it could still be wrong series
                            #use series year to break it down further.
                            logger.fdebug('COMIC-comicyear: ' + str(int(comic['ComicYear'])))
                            logger.fdebug('ARC-seriesyear: ' + str(int(arc['SeriesYear'])))
                            if int(comic['ComicYear']) != int(arc['SeriesYear']):
                                logger.fdebug("Series years are different - discarding match. " + str(comic['ComicYear']) + " != " + str(arc['SeriesYear']))
                            else:
                                logger.fdebug("issue #: " + str(arc['IssueNumber']) + " is present!")
                                logger.fdebug('isschk: ' + str(isschk))
                                logger.fdebug("Comicname: " + arc['ComicName'])
                                logger.fdebug("ComicID: " + str(isschk['ComicID']))
                                logger.fdebug("Issue: " + str(arc['IssueNumber']))
                                logger.fdebug("IssueArcID: " + str(arc['IssueArcID']))
                                #gather the matches now.
                                arc_match.append({
                                    "match_storyarc":          arc['StoryArc'],
                                    "match_name":              arc['ComicName'],
                                    "match_id":                isschk['ComicID'],
                                    "match_issue":             arc['IssueNumber'],
                                    "match_issuearcid":        arc['IssueArcID'],
                                    "match_seriesyear":        comic['ComicYear'],
                                    "match_readingorder":      arc['ReadingOrder'],
                                    "match_filedirectory":     comic['ComicLocation'],   #series directory path
                                    "destination_location":    dstloc})                  #path to given storyarc / grab-bag directory
                                matcheroso = "yes"
                                break
                if matcheroso == "no":
                    logger.fdebug("Unable to find a match for " + arc['ComicName'] + " :#" + arc['IssueNumber'])
                    wantedlist.append({
                         "ComicName":      arc['ComicName'],
                         "IssueNumber":    arc['IssueNumber'],
                         "IssueYear":      arc['IssueYear']})

                    if filelist is not None and mylar.STORYARCDIR:
                        fn = 0
                        valids = [x for x in filelist if re.sub('[\|\s]','', x['dynamic_name'].lower()).strip() == re.sub('[\|\s]','', arc['DynamicComicName'].lower()).strip()]
                        logger.info('valids: ' + str(valids))
                        if len(valids) > 0:
                            for tmpfc in filelist:
                                haveissue = "no"
                                issuedupe = "no"
                                temploc = tmpfc['issue_number'].replace('_', ' ')
                                fcdigit = helpers.issuedigits(arc['IssueNumber'])
                                int_iss = helpers.issuedigits(temploc)
                                if int_iss == fcdigit:
                                    logger.fdebug(arc['ComicName'] + ' Issue #' + arc['IssueNumber'] + ' already present in StoryArc directory.')
                                    #update readinglist db to reflect status.
                                    if mylar.READ2FILENAME:
                                        readorder = helpers.renamefile_readingorder(arc['ReadingOrder'])
                                        dfilename = str(readorder) + "-" + tmpfc['comicfilename']
                                    else:
                                        dfilename = tmpfc['comicfilename']

                                    if all([tmpfc['sub'] is not None, tmpfc['sub'] != 'None']):
                                        loc_path = os.path.join(tmpfc['ComicLocation'], tmpfc['sub'], dfilename)
                                    else:
                                        loc_path = os.path.join(tmpfc['ComicLocation'], dfilename)

                                    newVal = {"Status":   "Downloaded",
                                              "Location": loc_path}    #dfilename}
                                    ctrlVal = {"IssueArcID":  arc['IssueArcID']}
                                    myDB.upsert("readinglist", newVal, ctrlVal)
                                fn+=1
                    else:
                        newVal = {"Status":   "Skipped"}
                        ctrlVal = {"IssueArcID":  arc['IssueArcID']}
                        myDB.upsert("readinglist", newVal, ctrlVal)

            logger.fdebug("we matched on " + str(len(arc_match)) + " issues")
            for m_arc in arc_match:
                #now we cycle through the issues looking for a match.
                issue = myDB.selectone("SELECT * FROM issues where ComicID=? and Issue_Number=?", [m_arc['match_id'], m_arc['match_issue']]).fetchone()
                if issue is None: pass
                else:

                    logger.fdebug("issue: " + issue['Issue_Number'] + "..." + m_arc['match_issue'])
#                   if helpers.decimal_issue(issuechk['Issue_Number']) == helpers.decimal_issue(m_arc['match_issue']):
                    if issue['Issue_Number'] == m_arc['match_issue']:
                        logger.fdebug("we matched on " + issue['Issue_Number'] + " for " + m_arc['match_name'])
                        if issue['Status'] == 'Downloaded' or issue['Status'] == 'Archived' or issue['Status'] == 'Snatched':
                            if showonreadlist:
                                showctrlVal = {"IssueID":       issue['IssueID']}
                                shownewVal = {"ComicName":      issue['ComicName'],
                                              "Issue_Number":    issue['Issue_Number'],
                                              "IssueDate":      issue['IssueDate'],
                                              "SeriesYear":     m_arc['match_seriesyear'],
                                              "ComicID":        m_arc['match_id']}
                                myDB.upsert("readlist", shownewVal, showctrlVal)

                            logger.fdebug("Already have " + issue['ComicName'] + " :# " + issue['Issue_Number'])
                            if issue['Location'] is not None:
                                issloc = os.path.join(m_arc['match_filedirectory'], issue['Location'])
                            else:
                                issloc = None
                            location_path = issloc

                            if issue['Status'] == 'Downloaded':
                                #check multiple destination directory usage here.
                                if not os.path.isfile(issloc):
                                    if all([mylar.MULTIPLE_DEST_DIRS is not None, mylar.MULTIPLE_DEST_DIRS != 'None', os.path.join(mylar.MULTIPLE_DEST_DIRS, os.path.basename(m_arc['match_filedirectory'])) != issloc, os.path.exists(os.path.join(mylar.MULTIPLE_DEST_DIRS, os.path.basename(m_arc['match_filedirectory'])))]):
                                        issloc = os.path.join(mylar.MULTIPLE_DEST_DIRS, os.path.basename(m_arc['match_filedirectory']), issue['Location'])
                                        if not os.path.isfile(issloc):
                                            logger.warn('Source file cannot be located. Please do a Recheck for the specific series to ensure everything is correct.')
                                            continue

                                logger.fdebug('source location set to  : ' + issloc)

                                if all([mylar.STORYARCDIR, mylar.COPY2ARCDIR]):
                                    logger.fdebug('Destination location set to  : ' + m_arc['destination_location'])
                                    logger.fdebug('Attempting to copy into StoryArc directory')
                                    #copy into StoryArc directory...
                                    if mylar.READ2FILENAME:
                                        readorder = helpers.renamefile_readingorder(m_arc['match_readingorder'])
                                        dfilename = str(readorder) + "-" + issue['Location']
                                    else:
                                        dfilename = issue['Location']

                                    dstloc = os.path.join(m_arc['destination_location'], dfilename)

                                    if not os.path.isfile(dstloc):
                                        logger.fdebug('Copying ' + issloc + ' to ' + dstloc)
                                        try:
                                           fileoperation = helpers.file_ops(issloc, dstloc, arc=True)
                                           if not fileoperation:
                                               raise OSError
                                        except (OSError, IOError):
                                            logger.fdebug(module + ' Failed to ' + mylar.FILE_OPTS + ' ' + issloc + ' - check directories and manually re-run.')
                                            continue
                                    else:
                                        logger.fdebug('Destination file exists: ' + dstloc)
                                    location_path = dstloc
                                else:
                                    location_path = issloc

                            ctrlVal = {"IssueArcID":  m_arc['match_issuearcid']}
                            newVal = {'Status':   issue['Status'],
                                      'IssueID':  issue['IssueID'],
                                      'Location': location_path}

                            myDB.upsert("readinglist",newVal,ctrlVal)
               
                        else:
                            logger.fdebug("We don't have " + issue['ComicName'] + " :# " + issue['Issue_Number'])
                            ctrlVal = {"IssueArcID":  m_arc['match_issuearcid']}
                            newVal = {"Status":  "Wanted",
                                      "IssueID": issue['IssueID']}
                            myDB.upsert("readinglist", newVal, ctrlVal)
                            logger.info("Marked " + issue['ComicName'] + " :# " + issue['Issue_Number'] + " as Wanted.")

            return

    ArcWatchlist.exposed = True

    def SearchArcIssues(self, **kwargs):
        threading.Thread(target=self.ReadGetWanted, kwargs=kwargs).start()
    SearchArcIssues.exposed = True

    def ReadGetWanted(self, StoryArcID):
        # this will queue up (ie. make 'Wanted') issues in a given Story Arc that are 'Not Watched'
        #print StoryArcID
        stupdate = []
        mode = 'story_arc'
        myDB = db.DBConnection()
        wantedlist = myDB.select("SELECT * FROM readinglist WHERE StoryArcID=? AND Status is Null", [StoryArcID])
        if wantedlist is not None:
            for want in wantedlist:
                #print want
                issuechk = myDB.selectone("SELECT * FROM issues WHERE IssueID=?", [want['IssueArcID']]).fetchone()
                SARC = want['StoryArc']
                IssueArcID = want['IssueArcID']
                if issuechk is None:
                    # none means it's not a 'watched' series
                    s_comicid = want['ComicID'] #None
                    s_issueid = want['IssueID'] #None
                    stdate = want['StoreDate']
                    issdate = want['IssueDate']
                    logger.fdebug("-- NOT a watched series queue.")
                    logger.fdebug(want['ComicName'] + " -- #" + str(want['IssueNumber']))
                    logger.fdebug(u"Story Arc : " + str(SARC) + " queueing the selected issue...")
                    logger.fdebug(u"IssueArcID : " + str(IssueArcID))
                    logger.fdebug(u"ComicID: " + str(s_comicid) + " --- IssueID: " + str(s_issueid))  # no comicid in issues table.
                    logger.fdebug(u"StoreDate: " + str(stdate) + " --- IssueDate: " + str(issdate))
                    #logger.info(u'Publisher: ' + want['Publisher'])  <-- no publisher in issues table.
                    issueyear = want['IssueYEAR']
                    logger.fdebug('IssueYear: ' + str(issueyear))
                    if issueyear is None or issueyear == 'None':
                        try:
                            logger.fdebug('issdate:' + str(issdate))
                            issueyear = issdate[:4]
                            if not issueyear.startswith('19') and not issueyear.startswith('20'):
                                issueyear = stdate[:4]
                        except:
                            issueyear = stdate[:4]

                    logger.fdebug('ComicYear: ' + str(want['SeriesYear']))
                    foundcom, prov = search.search_init(ComicName=want['ComicName'], IssueNumber=want['IssueNumber'], ComicYear=issueyear, SeriesYear=want['SeriesYear'], Publisher=None, IssueDate=issdate, StoreDate=stdate, IssueID=s_issueid, SARC=SARC, IssueArcID=IssueArcID)
                else:
                    # it's a watched series
                    s_comicid = issuechk['ComicID']
                    s_issueid = issuechk['IssueID']
                    logger.fdebug("-- watched series queue.")
                    logger.fdebug(issuechk['ComicName'] + " -- #" + str(issuechk['Issue_Number']))
                    foundcom, prov = search.search_init(ComicName=issuechk['ComicName'], IssueNumber=issuechk['Issue_Number'], ComicYear=issuechk['IssueYear'], SeriesYear=issuechk['SeriesYear'], Publisher=None, IssueDate=None, StoreDate=issuechk['ReleaseDate'], IssueID=issuechk['IssueID'], AlternateSearch=None, UseFuzzy=None, ComicVersion=None, SARC=SARC, IssueArcID=IssueArcID)

                if foundcom == "yes":
                    logger.fdebug('sucessfully found.')
                    #update the status - this is necessary for torrents as they are in 'snatched' status.
                    updater.foundsearch(s_comicid, s_issueid, mode=mode, provider=prov, SARC=SARC, IssueArcID=IssueArcID)
                else:
                    logger.fdebug('not sucessfully found.')
                    stupdate.append({"Status":     "Wanted",
                                     "IssueArcID": IssueArcID,
                                     "IssueID":    s_issueid})

        watchlistchk = myDB.select("SELECT * FROM readinglist WHERE StoryArcID=? AND Status='Wanted'", [StoryArcID])
        if watchlistchk is not None:
            for watchchk in watchlistchk:
                logger.fdebug('Watchlist hit - ' + str(watchchk['ComicName']))
                issuechk = myDB.selectone("SELECT * FROM issues WHERE IssueID=?", [watchchk['IssueArcID']]).fetchone()
                SARC = watchchk['StoryArc']
                IssueArcID = watchchk['IssueArcID']
                if issuechk is None:
                    # none means it's not a 'watched' series
                    try:
                        s_comicid = watchchk['ComicID']
                    except:
                        s_comicid = None

                    try:
                        s_issueid = watchchk['IssueID']
                    except:
                        s_issueid = None

                    logger.fdebug("-- NOT a watched series queue.")
                    logger.fdebug(watchchk['ComicName'] + " -- #" + str(watchchk['IssueNumber']))
                    logger.fdebug(u"Story Arc : " + str(SARC) + " queueing up the selected issue...")
                    logger.fdebug(u"IssueArcID : " + str(IssueArcID))
                    try:
                        issueyear = watchchk['IssueYEAR']
                        logger.fdebug('issueYEAR : ' + issueyear)
                    except:
                        try:
                            issueyear = watchchk['IssueDate'][:4]
                        except:
                            issueyear = watchchk['StoreDate'][:4]

                    stdate = watchchk['StoreDate']
                    issdate = watchchk['IssueDate']
                    logger.fdebug('issueyear : ' + str(issueyear))
                    logger.fdebug('comicname : ' + watchchk['ComicName'])
                    logger.fdebug('issuenumber : ' + watchchk['IssueNumber'])
                    logger.fdebug('comicyear : ' + watchchk['SeriesYear'])
                    #logger.info('publisher : ' + watchchk['IssuePublisher']) <-- no publisher in table
                    logger.fdebug('SARC : ' + SARC)
                    logger.fdebug('IssueArcID : ' + IssueArcID)
                    foundcom, prov = search.search_init(ComicName=watchchk['ComicName'], IssueNumber=watchchk['IssueNumber'], ComicYear=issueyear, SeriesYear=watchchk['SeriesYear'], Publisher=None, IssueDate=issdate, StoreDate=stdate, IssueID=s_issueid, SARC=SARC, IssueArcID=IssueArcID)
                else:
                    # it's a watched series
                    s_comicid = issuechk['ComicID']
                    s_issueid = issuechk['IssueID']
                    logger.fdebug("-- watched series queue.")
                    logger.fdebug(issuechk['ComicName'] + " -- #" + str(issuechk['Issue_Number']))
                    foundcom, prov = search.search_init(ComicName=issuechk['ComicName'], IssueNumber=issuechk['Issue_Number'], ComicYear=issuechk['IssueYear'], SeriesYear=issuechk['SeriesYear'], Publisher=None, IssueDate=None, StoreDate=issuechk['ReleaseDate'], IssueID=issuechk['IssueID'], AlternateSearch=None, UseFuzzy=None, ComicVersion=None, SARC=SARC, IssueArcID=IssueArcID, mode=None, rsscheck=None, ComicID=None)
                if foundcom == "yes":
                    updater.foundsearch(s_comicid, s_issueid, mode=mode, provider=prov, SARC=SARC, IssueArcID=IssueArcID)
                else:
                    logger.fdebug('Watchlist issue not sucessfully found')
                    logger.fdebug('issuearcid: ' + str(IssueArcID))
                    logger.fdebug('issueid: ' + str(s_issueid))
                    stupdate.append({"Status":     "Wanted",
                                     "IssueArcID": IssueArcID,
                                     "IssueID":    s_issueid})

        if len(stupdate) > 0:
            logger.fdebug(str(len(stupdate)) + ' issues need to get updated to Wanted Status')
            for st in stupdate:
                ctrlVal = {'IssueArcID':  st['IssueArcID']}
                newVal = {'Status':   st['Status']}
                if st['IssueID']:
                    if st['IssueID']:
                        logger.fdebug('issueid:' + str(st['IssueID']))
                    newVal['IssueID'] = st['IssueID']
                myDB.upsert("readinglist", newVal, ctrlVal)
    ReadGetWanted.exposed = True


    def ReadMassCopy(self, StoryArcID, StoryArcName):
        #this copies entire story arcs into the /cache/<storyarc> folder
        #alternatively, it will copy the issues individually directly to a 3rd party device (ie.tablet)

        myDB = db.DBConnection()
        copylist = myDB.select("SELECT * FROM readlist WHERE StoryArcID=? AND Status='Downloaded'", [StoryArcID])
        if copylist is None:
            logger.fdebug("You don't have any issues from " + StoryArcName + ". Aborting Mass Copy.")
            return
        else:
            dst = os.path.join(mylar.CACHE_DIR, StoryArcName)
            for files in copylist:

                copyloc = files['Location']

    ReadMassCopy.exposed = True

    def logs(self):
        return serve_template(templatename="logs.html", title="Log", lineList=mylar.LOG_LIST)
    logs.exposed = True

    def clearLogs(self):
        mylar.LOG_LIST = []
        logger.info("Web logs cleared")
        raise cherrypy.HTTPRedirect("logs")
    clearLogs.exposed = True

    def toggleVerbose(self):
        mylar.VERBOSE = not mylar.VERBOSE
        logger.initLogger(console=not mylar.QUIET,
            log_dir=mylar.LOG_DIR, verbose=mylar.VERBOSE)
        logger.info("Verbose toggled, set to %s", mylar.VERBOSE)
        logger.debug("If you read this message, debug logging is available")
        raise cherrypy.HTTPRedirect("logs")
    toggleVerbose.exposed = True

    def getLog(self, iDisplayStart=0, iDisplayLength=100, iSortCol_0=0, sSortDir_0="desc", sSearch="", **kwargs):
        iDisplayStart = int(iDisplayStart)
        iDisplayLength = int(iDisplayLength)

        filtered = []
        if sSearch == "" or sSearch == None:
            filtered = mylar.LOG_LIST[::]
        else:
            filtered = [row for row in mylar.LOG_LIST for column in row if sSearch.lower() in column.lower()]
        sortcolumn = 0
        if iSortCol_0 == '1':
            sortcolumn = 2
        elif iSortCol_0 == '2':
            sortcolumn = 1
        filtered.sort(key=lambda x: x[sortcolumn], reverse=sSortDir_0 == "desc")

        rows = filtered[iDisplayStart:(iDisplayStart + iDisplayLength)]
        rows = [[row[0], row[2], row[1]] for row in rows]
        return json.dumps({
            'iTotalDisplayRecords': len(filtered),
            'iTotalRecords': len(mylar.LOG_LIST),
            'aaData': rows,
        })
    getLog.exposed = True

    def clearhistory(self, type=None):
        myDB = db.DBConnection()
        if type == 'all':
            logger.info(u"Clearing all history")
            myDB.action('DELETE from snatched')
        else:
            logger.info(u"Clearing history where status is %s" % type)
            myDB.action('DELETE from snatched WHERE Status=?', [type])
            if type == 'Processed':
                myDB.action("DELETE from snatched WHERE Status='Post-Processed'")
        raise cherrypy.HTTPRedirect("history")
    clearhistory.exposed = True

    def downloadLocal(self, IssueID=None, IssueArcID=None, ReadOrder=None, dir=None):
        myDB = db.DBConnection()
        issueDL = myDB.selectone("SELECT * FROM issues WHERE IssueID=?", [IssueID]).fetchone()
        comicid = issueDL['ComicID']
        #print ("comicid: " + str(comicid))
        comic = myDB.selectone("SELECT * FROM comics WHERE ComicID=?", [comicid]).fetchone()
        #---issue info
        comicname = comic['ComicName']
        issuenum = issueDL['Issue_Number']
        issuedate = issueDL['IssueDate']
        seriesyear = comic['ComicYear']
        #---
        issueLOC = comic['ComicLocation']
        #print ("IssueLOC: " + str(issueLOC))
        issueFILE = issueDL['Location']
        #print ("IssueFILE: "+ str(issueFILE))
        issuePATH = os.path.join(issueLOC, issueFILE)
        #print ("IssuePATH: " + str(issuePATH))

        # if dir is None, it's a normal copy to cache kinda thing.
        # if dir is a path, then it's coming from the pullist as the location to put all the weekly comics
        if dir is not None:
            dstPATH = dir
        else:
            dstPATH = os.path.join(mylar.CACHE_DIR, issueFILE)
        #print ("dstPATH: " + str(dstPATH))
        if IssueID:
            ISnewValueDict = {'inCacheDIR':  'True',
                            'Location':    issueFILE}

        if IssueArcID:
            if mylar.READ2FILENAME:
                #if it's coming from a StoryArc, check to see if we're appending the ReadingOrder to the filename
                ARCissueFILE = ReadOrder + "-" + issueFILE
                dstPATH = os.path.join(mylar.CACHE_DIR, ARCissueFILE)
                ISnewValueDict = {'inCacheDIR': 'True',
                                'Location':   issueFILE}

#            issueDL = myDB.action("SELECT * FROM readinglist WHERE IssueArcID=?", [IssueArcID]).fetchone()
#            storyarcid = issueDL['StoryArcID']
#            #print ("comicid: " + str(comicid))
#            issueLOC = mylar.DESTINATION_DIR
#            #print ("IssueLOC: " + str(issueLOC))
#            issueFILE = issueDL['Location']
#            #print ("IssueFILE: "+ str(issueFILE))
#            issuePATH = os.path.join(issueLOC,issueFILE)
#            #print ("IssuePATH: " + str(issuePATH))
#            dstPATH = os.path.join(mylar.CACHE_DIR, issueFILE)
#            #print ("dstPATH: " + str(dstPATH))

        try:
            shutil.copy2(issuePATH, dstPATH)
        except IOError as e:
            logger.error("Could not copy " + str(issuePATH) + " to " + str(dstPATH) + ". Copy to Cache terminated.")
            raise cherrypy.HTTPRedirect("comicDetails?ComicID=%s" % comicid)

        #logger.debug("sucessfully copied to cache...Enabling Download link")

        controlValueDict = {'IssueID': IssueID}
        RLnewValueDict = {'inCacheDIR':  'True',
                          'Location':    issueFILE,
                          'ComicID':     comicid,
                          'ComicName':   comicname,
                          'Issue_Number': issuenum,
                          'SeriesYear':  seriesyear,
                          'IssueDate':   issuedate}
        myDB.upsert("readlist", RLnewValueDict, controlValueDict)
        myDB.upsert("issues", ISnewValueDict, controlValueDict)
        if IssueArcID:
            controlValueD = {'IssueArcID':  IssueArcID}
            newValueDict = {'inCacheDIR': 'True',
                            'Location':   ARCissueFILE}
            myDB.upsert("readinglist", newValueDict, controlValueD)
        #print("DB updated - Download link now enabled.")

    downloadLocal.exposed = True

    def MassWeeklyDownload(self, pulldate, weekfolder=0, filename=None):
        if filename is None:
            mylar.WEEKFOLDER = int(weekfolder)
            mylar.config_write()
            raise cherrypy.HTTPRedirect("pullist")

        # this will download all downloaded comics from the weekly pull list and throw them
        # into a 'weekly' pull folder for those wanting to transfer directly to a 3rd party device.
        myDB = db.DBConnection()
        if mylar.WEEKFOLDER:
            if mylar.WEEKFOLDER_LOC:
                dstdir = mylar.WEEKFOLDER_LOC
            else:
                dstdir = mylar.DESTINATION_DIR
            import ast
            pulldate = ast.literal_eval(pulldate)
            logger.info('pulldate: ' + str(pulldate))
            if mylar.WEEKFOLDER_FORMAT == 0:
                #0 = YYYY-mm
                desdir = os.path.join(dstdir, str(pulldate['year']) + '-' + str(pulldate['weeknumber']))
            elif mylar.WEEKFOLDER_FORMAT == 1:
                #1 = YYYY-mm-dd (midweek)
                desdir = os.path.join(dstdir, str(pulldate['midweek']))

            chkdir = filechecker.validateAndCreateDirectory(desdir, create=True, module='WEEKLY-FOLDER')
            if not chkdir:
                logger.warn('Unable to create weekly directory. Check location & permissions. Aborting Copy.')
                return
        else:
            desdir = mylar.GRABBAG_DIR

        issuelist = helpers.listIssues(pulldate['weeknumber'],pulldate['year'])
        if issuelist is None:   # nothing on the list, just go go gone
            logger.info("There aren't any issues downloaded from this week yet.")
        else:
            iscount = 0
            for issue in issuelist:
                #logger.fdebug('Checking status of ' + issue['ComicName'] + ' #' + str(issue['Issue_Number']))
                if issue['Status'] == 'Downloaded':
                    logger.info('Status Downloaded.')
                    self.downloadLocal(issue['IssueID'], dir=desdir)
                    logger.info("Copied " + issue['ComicName'] + " #" + str(issue['Issue_Number']) + " to " + desdir.encode('utf-8').strip())
                    iscount+=1

            logger.info('I have copied ' + str(iscount) + ' issues from week #' + str(pulldate['weeknumber']) + ' pullist as requested.')
        raise cherrypy.HTTPRedirect("pullist?week=%s&year=%s" % (pulldate['weeknumber'], pulldate['year']))
    MassWeeklyDownload.exposed = True

    def idirectory(self):
        return serve_template(templatename="idirectory.html", title="Import a Directory")
    idirectory.exposed = True

    def confirmResult(self, comicname, comicid):
        #print ("here.")
        mode='series'
        sresults, explicit = mb.findComic(comicname, mode, None, explicit='all')
        #print sresults
        type='comic'
        return serve_template(templatename="searchresults.html", title='Import Results for: "' + comicname + '"', searchresults=sresults, type=type, imported='confirm', ogcname=comicid, explicit=explicit)
    confirmResult.exposed = True

    def Check_ImportStatus(self):
        #logger.info('import_status: ' + mylar.IMPORT_STATUS)
        return mylar.IMPORT_STATUS
    Check_ImportStatus.exposed = True

    def comicScan(self, path, scan=0, libraryscan=0, redirect=None, autoadd=0, imp_move=0, imp_rename=0, imp_metadata=0, forcescan=0):
        import Queue
        queue = Queue.Queue()

        #save the values so they stick.
        mylar.ADD_COMICS = autoadd
        mylar.COMIC_DIR = path
        mylar.IMP_MOVE = imp_move
        mylar.IMP_RENAME = imp_rename
        mylar.IMP_METADATA = imp_metadata
        mylar.config_write()

        logger.info('forcescan is: ' +  str(forcescan))
        if mylar.IMPORTLOCK and forcescan == 1:
            logger.info('Removing Current lock on import - if you do this AND another process is legitimately running, your causing your own problems.')
            mylar.IMPORTLOCK = False

        #thread the scan.
        if scan == '1':
            scan = True
            mylar.IMPORT_STATUS = 'Now starting the import'
            return self.ThreadcomicScan(scan, queue)
        else:
            scan = False
            return
    comicScan.exposed = True

    def ThreadcomicScan(self, scan, queue):
        thread_ = threading.Thread(target=librarysync.scanLibrary, name="LibraryScan", args=[scan, queue])
        thread_.start()
        thread_.join()
        chk = queue.get()
        while True:
            if chk[0]['result'] == 'success':
                yield chk[0]['result']
                logger.info('Successfully scanned in directory. Enabling the importResults button now.')
                mylar.IMPORTBUTTON = True   #globally set it to ON after the scan so that it will be picked up.
                mylar.IMPORT_STATUS = 'Import completed.'
                break
            else:
                yield ckh[0]['result']
                mylar.IMPORTBUTTON = False
                break
        return
    ThreadcomicScan.exposed = True

    def importResults(self):
        myDB = db.DBConnection()
        results = myDB.select("SELECT * FROM importresults WHERE WatchMatch is Null OR WatchMatch LIKE 'C%' group by DynamicName, Volume, Status COLLATE NOCASE")
        #this is to get the count of issues;
        res = []
        countit = []
        ann_cnt = 0
        for result in results:
            res.append(result)
        for x in res:
            if x['Volume']:
                #because Volume gets stored as NULL in the db, we need to account for it coming into here as a possible None value.
                countthis = myDB.select("SELECT count(*) FROM importresults WHERE DynamicName=? AND Volume=? AND Status=?", [x['DynamicName'],x['Volume'],x['Status']])
                countannuals = myDB.select("SELECT count(*) FROM importresults WHERE DynamicName=? AND Volume=? AND IssueNumber LIKE 'Annual%' AND Status=?", [x['DynamicName'],x['Volume'],x['Status']])
            else:
                countthis = myDB.select("SELECT count(*) FROM importresults WHERE DynamicName=? AND Volume IS NULL AND Status=?", [x['DynamicName'],x['Status']])
                countannuals = myDB.select("SELECT count(*) FROM importresults WHERE DynamicName=? AND Volume IS NULL AND IssueNumber LIKE 'Annual%' AND Status=?", [x['DynamicName'],x['Status']])
            countit.append({"DynamicName":  x['DynamicName'],
                            "Volume":       x['Volume'],
                            "IssueCount":   countthis[0][0],
                            "AnnualCount":  countannuals[0][0],
                            "ComicName":    x['ComicName'],
                            "DisplayName":  x['DisplayName'],
                            "Volume":       x['Volume'],
                            "ComicYear":    x['ComicYear'],
                            "Status":       x['Status'],
                            "ComicID":      x['ComicID'],
                            "WatchMatch":   x['WatchMatch'],
                            "ImportDate":   x['ImportDate'],
                            "SRID":         x['SRID']})

        return serve_template(templatename="importresults.html", title="Import Results", results=countit) #results, watchresults=watchresults)
    importResults.exposed = True

    def ImportFilelisting(self, comicname, dynamicname, volume):
        comicname = urllib.unquote_plus(helpers.econversion(comicname))
        dynamicname = helpers.econversion(urllib.unquote_plus(dynamicname)) #urllib.unquote(dynamicname).decode('utf-8')
        myDB = db.DBConnection()
        if volume is None or volume == 'None':
            results = myDB.select("SELECT * FROM importresults WHERE (WatchMatch is Null OR WatchMatch LIKE 'C%') AND DynamicName=? AND Volume IS NULL",[dynamicname])
        else:
            if not volume.lower().startswith('v'):
                volume = 'v' + str(volume)
            results = myDB.select("SELECT * FROM importresults WHERE (WatchMatch is Null OR WatchMatch LIKE 'C%') AND DynamicName=? AND Volume=?",[dynamicname,volume])

        filelisting = '<table width="500"><tr><td>'
        filelisting += '<center><b>Files that have been scanned in for:</b></center>'
        if volume is None or volume == 'None':
            filelisting += '<center><b>' + comicname + '</b></center></td></tr><tr><td>'
        else:
            filelisting += '<center><b>' + comicname + ' [' + str(volume) + ']</b></center></td></tr><tr><td>'
        #filelisting += '<div style="height:300px;overflow:scroll;overflow-x:hidden;">'
        filelisting += '<div style="display:inline-block;overflow-y:auto:overflow-x:hidden;">'
        cnt = 0
        for result in results:
            filelisting += result['ComicFilename'] + '</br>'
        filelisting += '</div></td></tr>'
        filelisting += '<tr><td align="right">' + str(len(results)) + ' Files.</td></tr>'
        filelisting += '</table>'
        return filelisting
    ImportFilelisting.exposed = True

    def deleteimport(self, ComicName, volume, DynamicName, Status):
        myDB = db.DBConnection()
        if volume is None or volume == 'None':
            logname = ComicName
        else:
            logname = ComicName + '[' + str(volume) + ']'
        logger.info("Removing import data for Comic: " + logname)
        if volume is None or volume == 'None':
            myDB.action('DELETE from importresults WHERE DynamicName=? AND Status=? AND (Volume is NULL OR Volume="None")', [DynamicName, Status])
        else:
            myDB.action('DELETE from importresults WHERE DynamicName=? AND Volume=? AND Status=?', [DynamicName, volume, Status])
        raise cherrypy.HTTPRedirect("importResults")
    deleteimport.exposed = True

    def preSearchit(self, ComicName, comiclist=None, mimp=0, volume=None, displaycomic=None, comicid=None, dynamicname=None, displayline=None):
        logger.info('here')
        if mylar.IMPORTLOCK:
            logger.info('There is an import already running. Please wait for it to finish, and then you can resubmit this import.')
            return
        importlock = threading.Lock()
        myDB = db.DBConnection()

        if mimp == 0:
            comiclist = []
            comiclist.append({"ComicName":   ComicName,
                              "DynamicName": dynamicname,
                              "Volume":      volume,
                              "ComicID":     comicid})

        with importlock:
            #set the global importlock here so that nothing runs and tries to refresh things simultaneously...
            mylar.IMPORTLOCK = True
            #do imports that have the comicID already present (ie. metatagging has returned valid hits).
            #if a comicID is present along with an IssueID - then we have valid metadata.
            #otherwise, comicID present by itself indicates a watch match that already exists and is done below this sequence.
            RemoveIDS = []
            for comicinfo in comiclist:
                logger.info('Checking for any valid ComicID\'s already present within filenames.')
                logger.info(comicinfo)
                if comicinfo['ComicID'] is None or comicinfo['ComicID'] == 'None':
                    continue
                else:
                    results = myDB.select("SELECT * FROM importresults WHERE (WatchMatch is Null OR WatchMatch LIKE 'C%') AND ComicID=?", [comicinfo['ComicID']])
                    files = []
                    for result in results:
                        files.append({'comicfilename': result['ComicFilename'],
                                      'comiclocation': result['ComicLocation'],
                                      'issuenumber':   result['IssueNumber'],
                                      'import_id':     result['impID']})

                    import random
                    SRID = str(random.randint(100000, 999999))

                    logger.info('Issues found with valid ComicID information for : ' + comicinfo['ComicName'] + ' [' + str(comicinfo['ComicID']) + ']')
                    imported = {'ComicName':     comicinfo['ComicName'],
                                'DynamicName':   comicinfo['DynamicName'],
                                'Volume':        comicinfo['Volume'],
                                'filelisting':   files,
                                'srid':          SRID}
                    self.addbyid(comicinfo['ComicID'], calledby=True, imported=imported, ogcname=comicinfo['ComicName'])

                    #status update.
                    ctrlVal = {"ComicID":     comicinfo['ComicID']}
                    newVal = {"Status":       'Imported',
                              "SRID":         SRID}
                    myDB.upsert("importresults", newVal, ctrlVal)
                    logger.info('Successfully verified import sequence data for : ' + comicinfo['ComicName'] + '. Currently adding to your watchlist.')
                    RemoveIDS.append(comicinfo['ComicID'])

            #we need to remove these items from the comiclist now, so they don't get processed again
            if len(RemoveIDS) > 0:
                for RID in RemoveIDS:
                    newlist = [k for k in comiclist if k['ComicID'] != RID]
                    comiclist = newlist

            for cl in comiclist:
                ComicName = cl['ComicName']
                volume = cl['Volume']
                DynamicName = cl['DynamicName']
                logger.fdebug('comicname: ' + ComicName)
                logger.fdebug('dyn: ' + DynamicName)

                if volume is None or volume == 'None':
                    comic_and_vol = ComicName
                else:
                    comic_and_vol = ComicName + ' (' + str(volume) + ')'
                logger.info('[' + comic_and_vol + '] Now preparing to import. First I need to determine the highest issue, and possible year(s) of the series.')
                if volume is None or volume == 'None':
                    logger.info('[none] dynamicname: ' + DynamicName)
                    logger.info('[none] volume: None')

                    results = myDB.select("SELECT * FROM importresults WHERE DynamicName=? AND Volume IS NULL AND Status='Not Imported'", [DynamicName])
                else:
                    logger.info('[!none] dynamicname: ' + DynamicName)
                    logger.info('[!none] volume: ' + volume)
                    results = myDB.select("SELECT * FROM importresults WHERE DynamicName=? AND Volume=? AND Status='Not Imported'", [DynamicName,volume])

                if not results:
                    logger.info('I cannot find any results for the given series. I should remove this from the list.')
                    continue
                #if results > 0:
                #    print ("There are " + str(results[7]) + " issues to import of " + str(ComicName))
                #build the valid year ranges and the minimum issue# here to pass to search.
                yearRANGE = []
                yearTOP = 0
                minISSUE = 0
                startISSUE = 10000000
                starttheyear = None
                comicstoIMP = []

                movealreadyonlist = "no"
                movedata = []

                for result in results:
                    if result is None:
                       break

                    if result['WatchMatch']:
                        watchmatched = result['WatchMatch']
                    else:
                        watchmatched = ''

                    if watchmatched.startswith('C'):
                        comicid = result['WatchMatch'][1:]
                        #since it's already in the watchlist, we just need to move the files and re-run the filechecker.
                        #self.refreshArtist(comicid=comicid,imported='yes')
                        if mylar.IMP_MOVE:
                            comloc = myDB.selectone("SELECT * FROM comics WHERE ComicID=?", [comicid]).fetchone()

                            movedata_comicid = comicid
                            movedata_comiclocation = comloc['ComicLocation']
                            movedata_comicname = ComicName
                            movealreadyonlist = "yes"
                            #mylar.moveit.movefiles(comicid,comloc['ComicLocation'],ComicName)
                            #check for existing files... (this is already called after move files in importer)
                            #updater.forceRescan(comicid)
                        else:
                            raise cherrypy.HTTPRedirect("importResults")
                    else:
                        comicstoIMP.append(result['ComicLocation'])#.decode(mylar.SYS_ENCODING, 'replace'))
                        getiss = result['IssueNumber']
                        #logger.info('getiss:' + getiss)
                        if 'annual' in getiss.lower():
                            tmpiss = re.sub('[^0-9]','', getiss).strip()
                            if any([tmpiss.startswith('19'), tmpiss.startswith('20')]) and len(tmpiss) == 4:
                                logger.fdebug('annual detected with no issue [' + getiss + ']. Skipping this entry for determining series length.')
                                continue
                        else:
                            if (result['ComicYear'] not in yearRANGE) or all([yearRANGE is None, yearRANGE == 'None']):
                                if result['ComicYear'] <> "0000" and result['ComicYear'] is not None:
                                    yearRANGE.append(str(result['ComicYear']))
                                    yearTOP = str(result['ComicYear'])
                            getiss_num = helpers.issuedigits(getiss)
                            miniss_num = helpers.issuedigits(minISSUE)
                            startiss_num = helpers.issuedigits(startISSUE)
                            if int(getiss_num) > int(miniss_num):
                                #logger.fdebug('Minimum issue now set to : ' + getiss + ' - it was : ' + minISSUE)
                                minISSUE = getiss
                            if int(getiss_num) < int(startiss_num):
                                #logger.fdebug('Start issue now set to : ' + getiss + ' - it was : ' + startISSUE)
                                startISSUE = str(getiss)
                                if helpers.issuedigits(startISSUE) == 1000 and result['ComicYear'] is not None:  # if it's an issue #1, get the year and assume that's the start.
                                    startyear = result['ComicYear']

                #taking this outside of the transaction in an attempt to stop db locking.
                if mylar.IMP_MOVE and movealreadyonlist == "yes":
                     mylar.moveit.movefiles(movedata_comicid, movedata_comiclocation, movedata_comicname)
                     updater.forceRescan(comicid)
                     raise cherrypy.HTTPRedirect("importResults")

                #figure out # of issues and the year range allowable
                logger.info('yearTOP: ' + str(yearTOP))
                logger.info('yearRANGE: ' + str(yearRANGE))
                if starttheyear is None:
                    if all([yearTOP != None, yearTOP != 'None']):
                        if int(str(yearTOP)) > 0:
                            minni = helpers.issuedigits(minISSUE)
                            logger.info(minni)
                            if minni < 1 or minni > 999999999:
                                logger.info('here')
                                maxyear = int(str(yearTOP))
                            else:
                                logger.info('there')
                                maxyear = int(str(yearTOP)) - ( (minni/1000) / 12 )
                            if str(maxyear) not in yearRANGE:
                                logger.info('maxyear:' + str(maxyear))
                                logger.info('yeartop:' + str(yearTOP))
                                for i in range(maxyear, int(yearTOP),1):
                                    if not any(int(x) == int(i) for x in yearRANGE):
                                        yearRANGE.append(str(i))
                        else:
                            yearRANGE = None
                    else:
                        yearRANGE = None
                else:
                    yearRANGE.append(starttheyear)

                if yearRANGE is not None:
                    yearRANGE = sorted(yearRANGE, reverse=True)
                #determine a best-guess to # of issues in series
                #this needs to be reworked / refined ALOT more.
                #minISSUE = highest issue #, startISSUE = lowest issue #
                numissues = len(comicstoIMP)
                logger.info('numissues: ' + str(numissues))
                ogcname = ComicName

                mode='series'
                displaycomic = helpers.filesafe(ComicName)
                displaycomic = re.sub('[\-]','', displaycomic).strip()
                displaycomic = re.sub('\s+', ' ', displaycomic).strip()
                logger.fdebug('displaycomic : ' + displaycomic)
                logger.fdebug('comicname : ' + ComicName)
                searchterm = '"' + displaycomic + '"'
                try:
                    if yearRANGE is None:
                        sresults, explicit = mb.findComic(searchterm, mode, issue=numissues, explicit='all') #ogcname, mode, issue=numissues, explicit='all') #ComicName, mode, issue=numissues)
                    else:
                        sresults, explicit = mb.findComic(searchterm, mode, issue=numissues, limityear=yearRANGE, explicit='all') #ogcname, mode, issue=numissues, limityear=yearRANGE, explicit='all') #ComicName, mode, issue=numissues, limityear=yearRANGE)
                except TypeError:
                    logger.warn('Comicvine API limit has been reached, and/or the comicvine website is not responding. Aborting process at this time, try again in an ~ hr when the api limit is reset.')
                    break

                type='comic'

                #we now need to cycle through the results until we get a hit on both dynamicname AND year (~count of issues possibly).
                logger.fdebug('[' + str(len(sresults)) + '] search results')
                search_matches = []
                for results in sresults:
                    rsn = filechecker.FileChecker()
                    rsn_run = rsn.dynamic_replace(results['name'])
                    result_name = rsn_run['mod_seriesname']
                    result_comicid = results['comicid']
                    result_year = results['comicyear']
                    if float(int(results['issues']) / 12):
                        totalissues = (int(results['issues']) / 12) + 1
                    else:
                        totalissues = int(results['issues']) / 12

                    totalyear_range = int(result_year) + totalissues    #2000 + (101 / 12) 2000 +8.4 = 2008
                    logger.fdebug('[' + str(totalyear_range) + '] Comparing: ' + re.sub('[\|\s]', '', DynamicName.lower()).strip() + ' - TO - ' + re.sub('[\|\s]', '', result_name.lower()).strip())
                    if any([str(totalyear_range) in results['seriesrange'], result_year in results['seriesrange']]):
                        logger.info('LastIssueID: ' + str(results['lastissueid']))
                        if re.sub('[\|\s]', '', DynamicName.lower()).strip() ==  re.sub('[\|\s]', '', result_name.lower()).strip():
                            logger.info('[IMPORT MATCH] ' + result_name + ' (' + str(result_comicid) + ')')
                            search_matches.append({'comicid':       results['comicid'],
                                                   'series':        results['name'],
                                                   'dynamicseries': result_name,
                                                   'seriesyear':    result_year,
                                                   'publisher':     results['publisher'],
                                                   'haveit':        results['haveit'],
                                                   'name':          results['name'],
                                                   'deck':          results['deck'],
                                                   'url':           results['url'],
                                                   'description':   results['description'],
                                                   'comicimage':    results['comicimage'],
                                                   'issues':        results['issues'],
                                                   'ogcname':       ogcname,
                                                   'comicyear':     results['comicyear']})

                if len(search_matches) == 1:
                    sr = search_matches[0]
                    logger.info("There is only one result...automagik-mode enabled for " + sr['series'] + " :: " + str(sr['comicid']))
                    resultset = 1
                else:
                    if len(search_matches) == 0 or len(search_matches) is None:
                        logger.fdebug("no results, removing the year from the agenda and re-querying.")
                        sresults, explicit = mb.findComic(searchterm, mode, issue=numissues, explicit='all') #ComicName, mode, issue=numissues)
                        logger.fdebug('[' + str(len(sresults)) + '] search results')
                        for results in sresults:
                            rsn = filechecker.FileChecker()
                            rsn_run = rsn.dynamic_replace(results['name'])
                            result_name = rsn_run['mod_seriesname']
                            result_comicid = results['comicid']
                            result_year = results['comicyear']
                            if float(int(results['issues']) / 12):
                                totalissues = (int(results['issues']) / 12) + 1
                            else:
                                totalissues = int(results['issues']) / 12

                            totalyear_range = int(result_year) + totalissues    #2000 + (101 / 12) 2000 +8.4 = 2008
                            logger.fdebug('[' + str(totalyear_range) + '] Comparing: ' + re.sub('[\|\s]', '', DynamicName.lower()).strip() + ' - TO - ' + re.sub('[\|\s]', '', result_name.lower()).strip())
                            if any([str(totalyear_range) in results['seriesrange'], result_year in results['seriesrange']]):
                                if re.sub('[\|\s]', '', DynamicName.lower()).strip() ==  re.sub('[\|\s]', '', result_name.lower()).strip():
                                    logger.info('[IMPORT MATCH] ' + result_name + ' (' + str(result_comicid) + ')')
                                    search_matches.append({'comicid':       results['comicid'],
                                                           'series':        results['name'],
                                                           'dynamicseries': result_name,
                                                           'seriesyear':    result_year,
                                                           'publisher':     results['publisher'],
                                                           'haveit':        results['haveit'],
                                                           'name':          results['name'],
                                                           'deck':          results['deck'],
                                                           'url':           results['url'],
                                                           'description':   results['description'],
                                                           'comicimage':    results['comicimage'],
                                                           'issues':        results['issues'],
                                                           'ogcname':       ogcname,
                                                           'comicyear':     results['comicyear']})

                        if len(search_matches) == 1:
                            sr = search_matches[0]
                            logger.info("There is only one result...automagik-mode enabled for " + sr['series'] + " :: " + str(sr['comicid']))
                            resultset = 1
                        else:
                            resultset = 0
                    else:
                        logger.info('Returning results to Select option - there are ' + str(len(search_matches)) + ' possibilities, manual intervention required.')
                        resultset = 0

                #generate random Search Results ID to allow for easier access for viewing logs / search results.

                import random
                SRID = str(random.randint(100000, 999999))

                    #link the SRID to the series that was just imported so that it can reference the search results when requested.

                if volume is None or volume == 'None':
                    ctrlVal = {"DynamicName": DynamicName,
                               "ComicName":   ComicName}
                else:
                    ctrlVal = {"DynamicName": DynamicName,
                               "ComicName":   ComicName,
                               "Volume":      volume}

                if len(sresults) > 1 or len(search_matches) > 1:
                    newVal = {"SRID":         SRID,
                              "Status":       'Manual Intervention'}
                else:
                    newVal = {"SRID":         SRID,
                              "Status":       'Importing'}

                myDB.upsert("importresults", newVal, ctrlVal)

                if len(search_matches) > 1:
                    # if we matched on more than one series above, just save those results instead of the entire search result set.
                    for sres in search_matches:
                        cVal = {"SRID":        SRID,
                                "comicid":     sres['comicid']}
                        #should store ogcname in here somewhere to account for naming conversions above.
                        nVal = {"Series":      ComicName,
                                "results":     len(search_matches),
                                "publisher":   sres['publisher'],
                                "haveit":      sres['haveit'],
                                "name":        sres['name'],
                                "deck":        sres['deck'],
                                "url":         sres['url'],
                                "description":  sres['description'],
                                "comicimage":  sres['comicimage'],
                                "issues":      sres['issues'],
                                "ogcname":     ogcname,
                               "comicyear":   sres['comicyear']}
                        myDB.upsert("searchresults", nVal, cVal)

                else:
                    # store the search results for series that returned more than one result for user to select later / when they want.
                    # should probably assign some random numeric for an id to reference back at some point.
                    for sres in sresults:
                        cVal = {"SRID":        SRID,
                                "comicid":     sres['comicid']}
                        #should store ogcname in here somewhere to account for naming conversions above.
                        nVal = {"Series":      ComicName,
                                "results":     len(sresults),
                                "publisher":   sres['publisher'],
                                "haveit":      sres['haveit'],
                                "name":        sres['name'],
                                "deck":        sres['deck'],
                                "url":         sres['url'],
                                "description":  sres['description'],
                                "comicimage":  sres['comicimage'],
                                "issues":      sres['issues'],
                                "ogcname":     ogcname,
                               "comicyear":   sres['comicyear']}
                        myDB.upsert("searchresults", nVal, cVal)

                if resultset == 1:
                    logger.info('now adding...')

                    if volume is None or volume == 'None':
                        results = myDB.select("SELECT * FROM importresults WHERE (WatchMatch is Null OR WatchMatch LIKE 'C%') AND DynamicName=? AND Volume IS NULL",[DynamicName])
                    else:
                        if not volume.lower().startswith('v'):
                            volume = 'v' + str(volume)
                        results = myDB.select("SELECT * FROM importresults WHERE (WatchMatch is Null OR WatchMatch LIKE 'C%') AND DynamicName=? AND Volume=?",[DynamicName,volume])
                    files = []
                    for result in results:
                        files.append({'comicfilename': result['ComicFilename'],
                                      'comiclocation': result['ComicLocation'],
                                      'issuenumber':   result['IssueNumber'],
                                      'import_id':     result['impID']})

                    imported = {'ComicName':     ComicName,
                                'DynamicName':   DynamicName,
                                'Volume':        volume,
                                'filelisting':   files,
                                'srid':          SRID}

                    self.addbyid(sr['comicid'], calledby=True, imported=imported, ogcname=ogcname)  #imported=yes)
                else:
                    logger.info('[IMPORT] There is more than one result that might be valid - normally this is due to the filename(s) not having enough information for me to use (ie. no volume label/year). Manual intervention is required.')
                    #force the status here just in case
                    newVal = {'SRID':     SRID,
                              'Status':   'Manual Intervention'}
                    myDB.upsert("importresults", newVal, ctrlVal)

        mylar.IMPORTLOCK = False
        logger.info('[IMPORT] Initial Import complete (I might still be populating the series data).')

    preSearchit.exposed = True

    def importresults_popup(self, SRID, ComicName, imported=None, ogcname=None, DynamicName=None, Volume=None):
        myDB = db.DBConnection()
        resultset = myDB.select("SELECT * FROM searchresults WHERE SRID=?", [SRID])
        if not resultset:
            logger.warn('There are no search results to view for this entry ' + ComicName + ' [' + str(SRID) + ']. Something is probably wrong.')
            raise cherrypy.HTTPRedirect("importResults")

        searchresults = resultset
        if any([Volume is None, Volume == 'None']):
            results = myDB.select("SELECT * FROM importresults WHERE (WatchMatch is Null OR WatchMatch LIKE 'C%') AND DynamicName=? AND Volume IS NULL",[DynamicName])
        else:
            if not Volume.lower().startswith('v'):
                volume = 'v' + str(Volume)
            else:
                volume = Volume
            results = myDB.select("SELECT * FROM importresults WHERE (WatchMatch is Null OR WatchMatch LIKE 'C%') AND DynamicName=? AND Volume=?",[DynamicName,volume])
        files = []
        for result in results:
            files.append({'comicfilename': result['ComicFilename'],
                          'comiclocation': result['ComicLocation'],
                          'issuenumber':   result['IssueNumber'],
                          'import_id':     result['impID']})

        imported = {'ComicName':     ComicName,
                    'DynamicName':   DynamicName,
                    'Volume':        Volume,
                    'filelisting':   files,
                    'srid':          SRID}

        return serve_template(templatename="importresults_popup.html", title="results", searchtext=ComicName, searchresults=searchresults, imported=imported)

    importresults_popup.exposed = True

    def pretty_git(self, br_history):
        #in order to 'prettify' the history log for display, we need to break it down so it's line by line.
        br_split = br_history.split("\n")  #split it on each commit
        for br in br_split:
            br_commit_st = br.find('-')  #first - will represent end of commit numeric
            br_commit = br[:br_commit_st].strip()
            br_time_en = br.replace('-', 'XXX', 1).find('-')  #2nd - is end of time datestamp
            br_time = br[br_commit_st +1:br_time_en].strip()
            print 'COMMIT:' + str(br_commit)
            print 'TIME:' + str(br_time)
            commit_split = br.split() #split it by space to break it further down..
            tag_chk = False
            statline = ''
            commit = []
            for cs in commit_split:
                if tag_chk == True:
                    if 'FIX:' in cs or 'IMP:' in cs:
                        commit.append({"commit":    br_commit,
                                       "time":      br_time,
                                       "stat":      tag_status,
                                       "line":      statline})
                        print commit
                        tag_chk == False
                        statline = ''
                    else:
                        statline += str(cs) + ' '
                else:
                    if 'FIX:' in cs:
                        tag_status = 'FIX'
                        tag_chk = True
                        print 'status: ' + str(tag_status)
                    elif 'IMP:' in cs:
                        tag_status = 'IMPROVEMENT'
                        tag_chk = True
                        print 'status: ' + str(tag_status)

    pretty_git.exposed = True
    #---
    def config(self):
        interface_dir = os.path.join(mylar.PROG_DIR, 'data/interfaces/')
        interface_list = [name for name in os.listdir(interface_dir) if os.path.isdir(os.path.join(interface_dir, name))]
#----
# to be implemented in the future.
#        branch_history, err = mylar.versioncheck.runGit("log --oneline --pretty=format:'%h - %ar - %s' -n 4")
#        #here we pass the branch_history to the pretty_git module to break it down
#        if branch_history:
#            self.pretty_git(branch_history)
#            br_hist = branch_history.replace("\n", "<br />\n")
#        else:
#            br_hist = err
#----
        myDB = db.DBConnection()
        CCOMICS = myDB.select("SELECT COUNT(*) FROM comics")
        CHAVES = myDB.select("SELECT COUNT(*) FROM issues WHERE Status='Downloaded' OR Status='Archived'")
        CISSUES = myDB.select("SELECT COUNT(*) FROM issues")
        CSIZE = myDB.select("select SUM(ComicSize) from issues where Status='Downloaded' or Status='Archived'")
        COUNT_COMICS = CCOMICS[0][0]
        COUNT_HAVES = CHAVES[0][0]
        COUNT_ISSUES = CISSUES[0][0]
        COUNT_SIZE = helpers.human_size(CSIZE[0][0])
        comicinfo = {"COUNT_COMICS": COUNT_COMICS,
                      "COUNT_HAVES": COUNT_HAVES,
                      "COUNT_ISSUES": COUNT_ISSUES,
                      "COUNT_SIZE": COUNT_SIZE}

        config = {
                    "comicvine_api": mylar.COMICVINE_API,
                    "http_host": mylar.HTTP_HOST,
                    "http_user": mylar.HTTP_USERNAME,
                    "http_port": mylar.HTTP_PORT,
                    "http_pass": mylar.HTTP_PASSWORD,
                    "enable_https": helpers.checked(mylar.ENABLE_HTTPS),
                    "https_cert": mylar.HTTPS_CERT,
                    "https_key": mylar.HTTPS_KEY,
                    "api_enabled": helpers.checked(mylar.API_ENABLED),
                    "api_key": mylar.API_KEY,
                    "launch_browser": helpers.checked(mylar.LAUNCH_BROWSER),
                    "auto_update": helpers.checked(mylar.AUTO_UPDATE),
                    "max_logsize": mylar.MAX_LOGSIZE,
                    "annuals_on": helpers.checked(mylar.ANNUALS_ON),
                    "enable_check_folder": helpers.checked(mylar.ENABLE_CHECK_FOLDER),
                    "check_folder": mylar.CHECK_FOLDER,
                    "download_scan_interval": mylar.DOWNLOAD_SCAN_INTERVAL,
                    "nzb_search_interval": mylar.SEARCH_INTERVAL,
                    "nzb_startup_search": helpers.checked(mylar.NZB_STARTUP_SEARCH),
                    "search_delay": mylar.SEARCH_DELAY,
                    "nzb_downloader_sabnzbd": helpers.radio(mylar.NZB_DOWNLOADER, 0),
                    "nzb_downloader_nzbget": helpers.radio(mylar.NZB_DOWNLOADER, 1),
                    "nzb_downloader_blackhole": helpers.radio(mylar.NZB_DOWNLOADER, 2),
                    "sab_host": mylar.SAB_HOST,
                    "sab_user": mylar.SAB_USERNAME,
                    "sab_api": mylar.SAB_APIKEY,
                    "sab_pass": mylar.SAB_PASSWORD,
                    "sab_cat": mylar.SAB_CATEGORY,
                    "sab_priority": mylar.SAB_PRIORITY,
                    "sab_directory": mylar.SAB_DIRECTORY,
                    "sab_to_mylar": helpers.checked(mylar.SAB_TO_MYLAR),
                    "nzbget_host": mylar.NZBGET_HOST,
                    "nzbget_port": mylar.NZBGET_PORT,
                    "nzbget_user": mylar.NZBGET_USERNAME,
                    "nzbget_pass": mylar.NZBGET_PASSWORD,
                    "nzbget_cat": mylar.NZBGET_CATEGORY,
                    "nzbget_priority": mylar.NZBGET_PRIORITY,
                    "nzbget_directory": mylar.NZBGET_DIRECTORY,
                    "torrent_downloader_watchlist": helpers.radio(mylar.TORRENT_DOWNLOADER, 0),
                    "torrent_downloader_utorrent": helpers.radio(mylar.TORRENT_DOWNLOADER, 1),
                    "torrent_downloader_rtorrent": helpers.radio(mylar.TORRENT_DOWNLOADER, 2),
                    "torrent_downloader_transmission": helpers.radio(mylar.TORRENT_DOWNLOADER, 3),
                    "torrent_downloader_deluge": helpers.radio(mylar.TORRENT_DOWNLOADER, 4),
                    "utorrent_host": mylar.UTORRENT_HOST,
                    "utorrent_username": mylar.UTORRENT_USERNAME,
                    "utorrent_password": mylar.UTORRENT_PASSWORD,
                    "utorrent_label": mylar.UTORRENT_LABEL,
                    "rtorrent_host": mylar.RTORRENT_HOST,
                    "rtorrent_rpc_url": mylar.RTORRENT_RPC_URL,
                    "rtorrent_authentication": mylar.RTORRENT_AUTHENTICATION,
                    "rtorrent_ssl": helpers.checked(mylar.RTORRENT_SSL),
                    "rtorrent_verify": helpers.checked(mylar.RTORRENT_VERIFY),
                    "rtorrent_username": mylar.RTORRENT_USERNAME,
                    "rtorrent_password": mylar.RTORRENT_PASSWORD,
                    "rtorrent_directory": mylar.RTORRENT_DIRECTORY,
                    "rtorrent_label": mylar.RTORRENT_LABEL,
                    "rtorrent_startonload": helpers.checked(mylar.RTORRENT_STARTONLOAD),
                    "transmission_host": mylar.TRANSMISSION_HOST,
                    "transmission_username": mylar.TRANSMISSION_USERNAME,
                    "transmission_password": mylar.TRANSMISSION_PASSWORD,
                    "transmission_directory": mylar.TRANSMISSION_DIRECTORY,
                    "deluge_host": mylar.DELUGE_HOST,
                    "deluge_username": mylar.DELUGE_USERNAME,
                    "deluge_password": mylar.DELUGE_PASSWORD,
                    "deluge_label": mylar.DELUGE_LABEL,
                    "blackhole_dir": mylar.BLACKHOLE_DIR,
                    "usenet_retention": mylar.USENET_RETENTION,
                    "use_nzbsu": helpers.checked(mylar.NZBSU),
                    "nzbsu_uid": mylar.NZBSU_UID,
                    "nzbsu_api": mylar.NZBSU_APIKEY,
                    "nzbsu_verify": helpers.checked(mylar.NZBSU_VERIFY),
                    "use_dognzb": helpers.checked(mylar.DOGNZB),
                    "dognzb_api": mylar.DOGNZB_APIKEY,
                    "dognzb_verify": helpers.checked(mylar.DOGNZB_VERIFY),
                    "use_experimental": helpers.checked(mylar.EXPERIMENTAL),
                    "enable_torznab": helpers.checked(mylar.ENABLE_TORZNAB),
                    "torznab_name": mylar.TORZNAB_NAME,
                    "torznab_host": mylar.TORZNAB_HOST,
                    "torznab_apikey": mylar.TORZNAB_APIKEY,
                    "torznab_category": mylar.TORZNAB_CATEGORY,
                    "use_newznab": helpers.checked(mylar.NEWZNAB),
                    "newznab_host": mylar.NEWZNAB_HOST,
                    "newznab_name": mylar.NEWZNAB_NAME,
                    "newznab_verify": helpers.checked(mylar.NEWZNAB_VERIFY),
                    "newznab_api": mylar.NEWZNAB_APIKEY,
                    "newznab_uid": mylar.NEWZNAB_UID,
                    "newznab_enabled": helpers.checked(mylar.NEWZNAB_ENABLED),
                    "extra_newznabs": mylar.EXTRA_NEWZNABS,
                    "enable_rss": helpers.checked(mylar.ENABLE_RSS),
                    "rss_checkinterval": mylar.RSS_CHECKINTERVAL,
                    "provider_order": mylar.PROVIDER_ORDER,
                    "enable_torrents": helpers.checked(mylar.ENABLE_TORRENTS),
                    "minseeds": mylar.MINSEEDS,
                    "torrent_local": helpers.checked(mylar.TORRENT_LOCAL),
                    "local_watchdir": mylar.LOCAL_WATCHDIR,
                    "torrent_seedbox": helpers.checked(mylar.TORRENT_SEEDBOX),
                    "seedbox_watchdir": mylar.SEEDBOX_WATCHDIR,
                    "seedbox_host": mylar.SEEDBOX_HOST,
                    "seedbox_port": mylar.SEEDBOX_PORT,
                    "seedbox_user": mylar.SEEDBOX_USER,
                    "seedbox_pass": mylar.SEEDBOX_PASS,
                    "enable_torrent_search": helpers.checked(mylar.ENABLE_TORRENT_SEARCH),
                    "enable_tpse": helpers.checked(mylar.ENABLE_TPSE),
                    "enable_32p": helpers.checked(mylar.ENABLE_32P),
                    "legacymode_32p": helpers.radio(mylar.MODE_32P, 0),
                    "authmode_32p": helpers.radio(mylar.MODE_32P, 1),
                    "rssfeed_32p": mylar.RSSFEED_32P,
                    "passkey_32p": mylar.PASSKEY_32P,
                    "username_32p": mylar.USERNAME_32P,
                    "password_32p": mylar.PASSWORD_32P,
                    "snatchedtorrent_notify": helpers.checked(mylar.SNATCHEDTORRENT_NOTIFY),
                    "destination_dir": mylar.DESTINATION_DIR,
                    "create_folders": helpers.checked(mylar.CREATE_FOLDERS),
                    "enforce_perms": helpers.checked(mylar.ENFORCE_PERMS),
                    "chmod_dir": mylar.CHMOD_DIR,
                    "chmod_file": mylar.CHMOD_FILE,
                    "chowner": mylar.CHOWNER,
                    "chgroup": mylar.CHGROUP,
                    "replace_spaces": helpers.checked(mylar.REPLACE_SPACES),
                    "replace_char": mylar.REPLACE_CHAR,
                    "use_minsize": helpers.checked(mylar.USE_MINSIZE),
                    "minsize": mylar.MINSIZE,
                    "use_maxsize": helpers.checked(mylar.USE_MAXSIZE),
                    "maxsize": mylar.MAXSIZE,
                    "interface_list": interface_list,
                    "dupeconstraint": mylar.DUPECONSTRAINT,
                    "ddump": helpers.checked(mylar.DDUMP),
                    "duplicate_dump": mylar.DUPLICATE_DUMP,
                    "autowant_all": helpers.checked(mylar.AUTOWANT_ALL),
                    "autowant_upcoming": helpers.checked(mylar.AUTOWANT_UPCOMING),
                    "comic_cover_local": helpers.checked(mylar.COMIC_COVER_LOCAL),
                    "pref_qual_0": helpers.radio(int(mylar.PREFERRED_QUALITY), 0),
                    "pref_qual_1": helpers.radio(int(mylar.PREFERRED_QUALITY), 1),
                    "pref_qual_2": helpers.radio(int(mylar.PREFERRED_QUALITY), 2),
                    "move_files": helpers.checked(mylar.MOVE_FILES),
                    "rename_files": helpers.checked(mylar.RENAME_FILES),
                    "folder_format": mylar.FOLDER_FORMAT,
                    "file_format": mylar.FILE_FORMAT,
                    "zero_level": helpers.checked(mylar.ZERO_LEVEL),
                    "zero_level_n": mylar.ZERO_LEVEL_N,
                    "add_to_csv": helpers.checked(mylar.ADD_TO_CSV),
                    "cvinfo": helpers.checked(mylar.CVINFO),
                    "lowercase_filenames": helpers.checked(mylar.LOWERCASE_FILENAMES),
                    "syno_fix": helpers.checked(mylar.SYNO_FIX),
                    "prowl_enabled": helpers.checked(mylar.PROWL_ENABLED),
                    "prowl_onsnatch": helpers.checked(mylar.PROWL_ONSNATCH),
                    "prowl_keys": mylar.PROWL_KEYS,
                    "prowl_priority": mylar.PROWL_PRIORITY,
                    "nma_enabled": helpers.checked(mylar.NMA_ENABLED),
                    "nma_apikey": mylar.NMA_APIKEY,
                    "nma_priority": int(mylar.NMA_PRIORITY),
                    "nma_onsnatch": helpers.checked(mylar.NMA_ONSNATCH),
                    "pushover_enabled": helpers.checked(mylar.PUSHOVER_ENABLED),
                    "pushover_onsnatch": helpers.checked(mylar.PUSHOVER_ONSNATCH),
                    "pushover_apikey": mylar.PUSHOVER_APIKEY,
                    "pushover_userkey": mylar.PUSHOVER_USERKEY,
                    "pushover_priority": mylar.PUSHOVER_PRIORITY,
                    "boxcar_enabled": helpers.checked(mylar.BOXCAR_ENABLED),
                    "boxcar_onsnatch": helpers.checked(mylar.BOXCAR_ONSNATCH),
                    "boxcar_token": mylar.BOXCAR_TOKEN,
                    "pushbullet_enabled": helpers.checked(mylar.PUSHBULLET_ENABLED),
                    "pushbullet_onsnatch": helpers.checked(mylar.PUSHBULLET_ONSNATCH),
                    "pushbullet_apikey": mylar.PUSHBULLET_APIKEY,
                    "pushbullet_deviceid": mylar.PUSHBULLET_DEVICEID,
                    "telegram_enabled": helpers.checked(mylar.TELEGRAM_ENABLED),
                    "telegram_onsnatch": helpers.checked(mylar.TELEGRAM_ONSNATCH),
                    "telegram_token": mylar.TELEGRAM_TOKEN,
                    "telegram_userid": mylar.TELEGRAM_USERID,
                    "enable_extra_scripts": helpers.checked(mylar.ENABLE_EXTRA_SCRIPTS),
                    "extra_scripts": mylar.EXTRA_SCRIPTS,
                    "post_processing": helpers.checked(mylar.POST_PROCESSING),
                    "file_opts": mylar.FILE_OPTS,
                    "enable_meta": helpers.checked(mylar.ENABLE_META),
                    "cbr2cbz_only": helpers.checked(mylar.CBR2CBZ_ONLY),
                    "cmtagger_path": mylar.CMTAGGER_PATH,
                    "ct_tag_cr": helpers.checked(mylar.CT_TAG_CR),
                    "ct_tag_cbl": helpers.checked(mylar.CT_TAG_CBL),
                    "ct_cbz_overwrite": helpers.checked(mylar.CT_CBZ_OVERWRITE),
                    "unrar_cmd": mylar.UNRAR_CMD,
                    "failed_download_handling": helpers.checked(mylar.FAILED_DOWNLOAD_HANDLING),
                    "failed_auto": helpers.checked(mylar.FAILED_AUTO),
                    "branch": mylar.GIT_BRANCH,
                    "br_type": mylar.INSTALL_TYPE,
                    "br_version": mylar.versioncheck.getVersion()[0],
                    "py_version": platform.python_version(),
                    "data_dir": mylar.DATA_DIR,
                    "prog_dir": mylar.PROG_DIR,
                    "cache_dir": mylar.CACHE_DIR,
                    "config_file": mylar.CONFIG_FILE,
                    "branch_history": 'None',
#                    "branch_history" : br_hist,
                    "enable_pre_scripts": helpers.checked(mylar.ENABLE_PRE_SCRIPTS),
                    "pre_scripts": mylar.PRE_SCRIPTS,
                    "log_dir": mylar.LOG_DIR
               }
        return serve_template(templatename="config.html", title="Settings", config=config, comicinfo=comicinfo)
    config.exposed = True

    def error_change(self, comicid, errorgcd, comicname, comicyear, imported=None, mogcname=None):
        # if comicname contains a "," it will break the exceptions import.
        import urllib
        b = urllib.unquote_plus(comicname)
#        cname = b.decode("utf-8")
        cname = b.encode('utf-8')
        cname = re.sub("\,", "", cname)

        if mogcname != None:
            c = urllib.unquote_plus(mogcname)
            ogcname = c.encode('utf-8')
        else:
            ogcname = None

        if errorgcd[:5].isdigit():
            logger.info("GCD-ID detected : " + str(errorgcd)[:5])
            logger.info("ogcname: " + str(ogcname))
            logger.info("I'm assuming you know what you're doing - going to force-match for " + cname)
            self.from_Exceptions(comicid=comicid, gcdid=errorgcd, comicname=cname, comicyear=comicyear, imported=imported, ogcname=ogcname)
        else:
            logger.info("Assuming rewording of Comic - adjusting to : " + str(errorgcd))
            Err_Info = mylar.cv.getComic(comicid, 'comic')
            self.addComic(comicid=comicid, comicname=str(errorgcd), comicyear=Err_Info['ComicYear'], comicissues=Err_Info['ComicIssues'], comicpublisher=Err_Info['ComicPublisher'])

    error_change.exposed = True

    def manual_annual_add(self, manual_comicid, comicname, comicyear, comicid, x=None, y=None):
        import urllib
        b = urllib.unquote_plus(comicname)
        cname = b.encode('utf-8')

        logger.fdebug('comicid to be attached : ' + str(manual_comicid))
        logger.fdebug('comicname : ' + str(cname))
        logger.fdebug('comicyear : ' + str(comicyear))
        logger.fdebug('comicid : ' + str(comicid))
        issueid = manual_comicid
        logger.fdebug('I will be adding ' + str(issueid) + ' to the Annual list for this series.')
        threading.Thread(target=importer.manualAnnual, args=[manual_comicid, cname, comicyear, comicid]).start()

        raise cherrypy.HTTPRedirect("comicDetails?ComicID=%s" % comicid)
    manual_annual_add.exposed = True

    def comic_config(self, com_location, ComicID, alt_search=None, fuzzy_year=None, comic_version=None, force_continuing=None, alt_filename=None, allow_packs=None, corrected_seriesyear=None):
        myDB = db.DBConnection()
#--- this is for multiple search terms............
#--- works, just need to redo search.py to accomodate multiple search terms
        ffs_alt = []
        if '##' in alt_search:
            ffs = alt_search.find('##')
            ffs_alt.append(alt_search[:ffs])
            ffs_alt_st = str(ffs_alt[0])
            logger.fdebug("ffs_alt: " + str(ffs_alt[0]))

        ffs_test = alt_search.split('##')
        if len(ffs_test) > 0:
            logger.fdebug("ffs_test names: " + str(len(ffs_test)))
            ffs_count = len(ffs_test)
            n=1
            while (n < ffs_count):
                ffs_alt.append(ffs_test[n])
                logger.fdebug("adding : " + str(ffs_test[n]))
               #print("ffs_alt : " + str(ffs_alt))
                ffs_alt_st = str(ffs_alt_st) + "..." + str(ffs_test[n])
                n+=1
            asearch = ffs_alt
        else:
            asearch = alt_search

#        ffs_alt = []
#        if '+' in alt_search:
            #find first +
#            ffs = alt_search.find('+')
#            ffs_alt.append(alt_search[:ffs])
#            ffs_alt_st = str(ffs_alt[0])
#            print("ffs_alt: " + str(ffs_alt[0]))

            # split the entire string by the delimter +
#            ffs_test = alt_search.split('+')
#            if len(ffs_test) > 0:
#                print("ffs_test names: " + str(len(ffs_test)))
#                ffs_count = len(ffs_test)
#                n=1
#                while (n < ffs_count):
#                    ffs_alt.append(ffs_test[n])
#                    print("adding : " + str(ffs_test[n]))
                    #print("ffs_alt : " + str(ffs_alt))
#                    ffs_alt_st = str(ffs_alt_st) + "..." + str(ffs_test[n])
#                    n+=1
#            asearch = ffs_alt
#        else:
#            asearch = alt_search
        asearch = str(alt_search)

        controlValueDict = {'ComicID': ComicID}
        newValues = {"ComicLocation":        com_location}
                     #"QUALalt_vers":         qual_altvers,
                     #"QUALScanner":          qual_scanner,
                     #"QUALtype":             qual_type,
                     #"QUALquality":          qual_quality
                     #}
        if asearch is not None:
            if re.sub(r'\s', '', asearch) == '':
                newValues['AlternateSearch'] = "None"
            else:
                newValues['AlternateSearch'] = str(asearch)
        else:
            newValues['AlternateSearch'] = "None"

        if fuzzy_year is None:
            newValues['UseFuzzy'] = "0"
        else:
            newValues['UseFuzzy'] = str(fuzzy_year)

        if corrected_seriesyear is not None:
            newValues['Corrected_SeriesYear'] = str(corrected_seriesyear)
            newValues['ComicYear'] = str(corrected_seriesyear)

        if comic_version is None or comic_version == 'None':
            newValues['ComicVersion'] = "None"
        else:
            if comic_version[1:].isdigit() and comic_version[:1].lower() == 'v':
                newValues['ComicVersion'] = str(comic_version)
            else:
                logger.info("Invalid Versioning entered - it must be in the format of v#")
                newValues['ComicVersion'] = "None"

        if force_continuing is None:
            newValues['ForceContinuing'] = 0
        else:
            newValues['ForceContinuing'] = 1

        if allow_packs is None:
            newValues['AllowPacks'] = 0
        else:
            newValues['AllowPacks'] = 1

        if alt_filename is None or alt_filename == 'None':
            newValues['AlternateFileName'] = "None"
        else:
            newValues['AlternateFileName'] = str(alt_filename)

        #force the check/creation of directory com_location here
        if os.path.isdir(str(com_location)):
            logger.info(u"Validating Directory (" + str(com_location) + "). Already exists! Continuing...")
        else:
            logger.fdebug("Updated Directory doesn't exist! - attempting to create now.")
            #try:
            #    os.makedirs(str(com_location))
            #    logger.info(u"Directory successfully created at: " + str(com_location))
            #except OSError:
            #    logger.error(u"Could not create comicdir : " + str(com_location))
            checkdirectory = filechecker.validateAndCreateDirectory(com_location, True)
            if not checkdirectory:
                logger.warn('Error trying to validate/create directory. Aborting this process at this time.')
                return

        myDB.upsert("comics", newValues, controlValueDict)
        raise cherrypy.HTTPRedirect("comicDetails?ComicID=%s" % ComicID)
    comic_config.exposed = True

    def readlistOptions(self, send2read=0, tab_enable=0, tab_host=None, tab_user=None, tab_pass=None, tab_directory=None, maintainseriesfolder=0):
        mylar.SEND2READ = int(send2read)
        mylar.MAINTAINSERIESFOLDER = int(maintainseriesfolder)
        mylar.TAB_ENABLE = int(tab_enable)
        mylar.TAB_HOST = tab_host
        mylar.TAB_USER = tab_user
        mylar.TAB_PASS = tab_pass
        mylar.TAB_DIRECTORY = tab_directory
        mylar.config_write()

        raise cherrypy.HTTPRedirect("readlist")

    readlistOptions.exposed = True

    def arcOptions(self, StoryArcID=None, StoryArcName=None, read2filename=0, storyarcdir=0, arc_folderformat=None, copy2arcdir=0, arc_fileops='copy'):
        mylar.READ2FILENAME = int(read2filename)
        mylar.STORYARCDIR = int(storyarcdir)
        mylar.ARC_FOLDERFORMAT = arc_folderformat
        mylar.COPY2ARCDIR = int(copy2arcdir)
        mylar.ARC_FILEOPS = arc_fileops
        mylar.config_write()
        logger.info(mylar.ARC_FOLDERFORMAT)

        #force the check/creation of directory com_location here
        #if mylar.STORYARCDIR:
        #    arcdir = os.path.join(mylar.DESTINATION_DIR, 'StoryArcs')
        #    if os.path.isdir(str(arcdir)):
        #        logger.info(u"Validating Directory (" + str(arcdir) + "). Already exists! Continuing...")
        #    else:
        #        logger.fdebug("Updated Directory doesn't exist! - attempting to create now.")
        #        checkdirectory = filechecker.validateAndCreateDirectory(arcdir, True)
        #        if not checkdirectory:
        #            logger.warn('Error trying to validate/create directory. Aborting this process at this time.')
        #            return
        if StoryArcID is not None:
            raise cherrypy.HTTPRedirect("detailStoryArc?StoryArcID=%s&StoryArcName=%s" % (StoryArcID, StoryArcName))
        else:
            raise cherrypy.HTTPRedirect("storyarc_main")
    arcOptions.exposed = True


    def configUpdate(self, comicvine_api=None, http_host='0.0.0.0', http_username=None, http_port=8090, http_password=None, enable_https=0, https_cert=None, https_key=None, api_enabled=0, api_key=None, launch_browser=0, auto_update=0, annuals_on=0, max_logsize=None, download_scan_interval=None, nzb_search_interval=None, nzb_startup_search=0,
        nzb_downloader=0, sab_host=None, sab_username=None, sab_apikey=None, sab_password=None, sab_category=None, sab_priority=None, sab_directory=None, sab_to_mylar=0, log_dir=None, log_level=0, blackhole_dir=None,
        nzbget_host=None, nzbget_port=None, nzbget_username=None, nzbget_password=None, nzbget_category=None, nzbget_priority=None, nzbget_directory=None,
        usenet_retention=None, nzbsu=0, nzbsu_uid=None, nzbsu_apikey=None, nzbsu_verify=0, dognzb=0, dognzb_apikey=None, dognzb_verify=0, newznab=0, newznab_host=None, newznab_name=None, newznab_verify=0, newznab_apikey=None, newznab_uid=None, newznab_enabled=0,
        enable_torznab=0, torznab_name=None, torznab_host=None, torznab_apikey=None, torznab_category=None, experimental=0, check_folder=None, enable_check_folder=0,
        enable_meta=0, cbr2cbz_only=0, cmtagger_path=None, ct_tag_cr=0, ct_tag_cbl=0, ct_cbz_overwrite=0, unrar_cmd=None, enable_rss=0, rss_checkinterval=None, failed_download_handling=0, failed_auto=0, enable_torrent_search=0, enable_tpse=0, enable_32p=0, mode_32p=0, rssfeed_32p=None, passkey_32p=None, username_32p=None, password_32p=None, snatchedtorrent_notify=0,
        enable_torrents=0, minseeds=0, local_watchdir=None, seedbox_watchdir=None, seedbox_user=None, seedbox_pass=None, seedbox_host=None, seedbox_port=None,
        prowl_enabled=0, prowl_onsnatch=0, prowl_keys=None, prowl_priority=None, nma_enabled=0, nma_apikey=None, nma_priority=0, nma_onsnatch=0, pushover_enabled=0, pushover_onsnatch=0, pushover_apikey=None, pushover_userkey=None, pushover_priority=None, boxcar_enabled=0, boxcar_onsnatch=0, boxcar_token=None,
        pushbullet_enabled=0, pushbullet_apikey=None, pushbullet_deviceid=None, pushbullet_onsnatch=0, telegram_enabled=0, telegram_token=None, telegram_userid=None, telegram_onsnatch=0, torrent_downloader=0, torrent_local=0, torrent_seedbox=0, utorrent_host=None, utorrent_username=None, utorrent_password=None, utorrent_label=None,
        rtorrent_host=None, rtorrent_ssl=0, rtorrent_verify=0, rtorrent_authentication='basic', rtorrent_rpc_url=None, rtorrent_username=None, rtorrent_password=None, rtorrent_directory=None, rtorrent_label=None, rtorrent_startonload=0, transmission_host=None, transmission_username=None, transmission_password=None, transmission_directory=None,deluge_host=None, deluge_username=None, deluge_password=None, deluge_label=None,
        preferred_quality=0, move_files=0, rename_files=0, add_to_csv=1, cvinfo=0, lowercase_filenames=0, folder_format=None, file_format=None, enable_extra_scripts=0, extra_scripts=None, enable_pre_scripts=0, pre_scripts=None, post_processing=0, file_opts=None, syno_fix=0, search_delay=None, enforce_perms=0, chmod_dir=0777, chmod_file=0660, chowner=None, chgroup=None,
        tsab=None, destination_dir=None, create_folders=1, replace_spaces=0, replace_char=None, use_minsize=0, minsize=None, use_maxsize=0, maxsize=None, autowant_all=0, autowant_upcoming=0, comic_cover_local=0, zero_level=0, zero_level_n=None, interface=None, dupeconstraint=None, ddump=0, duplicate_dump=None, **kwargs):
        mylar.COMICVINE_API = comicvine_api
        mylar.HTTP_HOST = http_host
        mylar.HTTP_PORT = http_port
        mylar.HTTP_USERNAME = http_username
        mylar.HTTP_PASSWORD = http_password
        mylar.ENABLE_HTTPS = enable_https
        mylar.HTTPS_CERT = https_cert
        mylar.HTTPS_KEY = https_key
        mylar.API_ENABLED = api_enabled
        mylar.API_KEY = api_key
        mylar.LAUNCH_BROWSER = launch_browser
        mylar.AUTO_UPDATE = auto_update
        mylar.ANNUALS_ON = int(annuals_on)
        mylar.MAX_LOGSIZE = max_logsize
        mylar.ENABLE_CHECK_FOLDER = enable_check_folder
        mylar.CHECK_FOLDER = check_folder
        mylar.DOWNLOAD_SCAN_INTERVAL = download_scan_interval
        mylar.SEARCH_INTERVAL = nzb_search_interval
        mylar.NZB_STARTUP_SEARCH = nzb_startup_search
        mylar.SEARCH_DELAY = search_delay
        mylar.NZB_DOWNLOADER = int(nzb_downloader)
        if tsab:
            self.SABtest(sab_host, sab_username, sab_password, sab_apikey)
        else:
            mylar.SAB_HOST = sab_host
            mylar.SAB_USERNAME = sab_username
            mylar.SAB_PASSWORD = sab_password
            mylar.SAB_APIKEY = sab_apikey
        mylar.SAB_CATEGORY = sab_category
        mylar.SAB_PRIORITY = sab_priority
        mylar.SAB_TO_MYLAR = sab_to_mylar
        mylar.SAB_DIRECTORY = sab_directory
        mylar.NZBGET_HOST = nzbget_host
        mylar.NZBGET_USERNAME = nzbget_username
        mylar.NZBGET_PASSWORD = nzbget_password
        mylar.NZBGET_PORT = nzbget_port
        mylar.NZBGET_CATEGORY = nzbget_category
        mylar.NZBGET_PRIORITY = nzbget_priority
        mylar.NZBGET_DIRECTORY = nzbget_directory
        mylar.BLACKHOLE_DIR = blackhole_dir
        mylar.USENET_RETENTION = usenet_retention
        mylar.NZBSU = nzbsu
        mylar.NZBSU_UID = nzbsu_uid
        mylar.NZBSU_APIKEY = nzbsu_apikey
        mylar.NZBSU_VERIFY = nzbsu_verify
        mylar.DOGNZB = dognzb
        mylar.DOGNZB_APIKEY = dognzb_apikey
        mylar.DOGNZB_VERIFYY = dognzb_verify
        mylar.ENABLE_TORZNAB = enable_torznab
        mylar.TORZNAB_NAME = torznab_name
        mylar.TORZNAB_HOST = torznab_host
        mylar.TORZNAB_APIKEY = torznab_apikey
        mylar.TORZNAB_CATEGORY = torznab_category
        mylar.EXPERIMENTAL = experimental
        mylar.NEWZNAB = newznab
        #mylar.NEWZNAB_HOST = newznab_host
        #mylar.NEWZNAB_APIKEY = newznab_apikey
        #mylar.NEWZNAB_ENABLED = newznab_enabled
        mylar.ENABLE_RSS = int(enable_rss)
        mylar.RSS_CHECKINTERVAL = rss_checkinterval
        mylar.ENABLE_TORRENTS = int(enable_torrents)
        mylar.MINSEEDS = int(minseeds)
        mylar.TORRENT_DOWNLOADER = int(torrent_downloader)
        mylar.TORRENT_LOCAL = int(torrent_local)
        mylar.LOCAL_WATCHDIR = local_watchdir
        mylar.TORRENT_SEEDBOX = int(torrent_seedbox)
        mylar.SEEDBOX_WATCHDIR = seedbox_watchdir
        mylar.SEEDBOX_HOST = seedbox_host
        mylar.SEEDBOX_PORT = seedbox_port
        mylar.SEEDBOX_USER = seedbox_user
        mylar.SEEDBOX_PASS = seedbox_pass
        mylar.UTORRENT_HOST = utorrent_host
        mylar.UTORRENT_USERNAME = utorrent_username
        mylar.UTORRENT_PASSWORD = utorrent_password
        mylar.UTORRENT_LABEL = utorrent_label
        mylar.RTORRENT_HOST = rtorrent_host
        mylar.RTORRENT_AUTHENTICATION = rtorrent_authentication
        mylar.RTORRENT_SSL = rtorrent_ssl
        mylar.RTORRENT_VERIFY = rtorrent_verify
        mylar.RTORRENT_RPC_URL = rtorrent_rpc_url
        mylar.RTORRENT_USERNAME = rtorrent_username
        mylar.RTORRENT_PASSWORD = rtorrent_password
        mylar.RTORRENT_DIRECTORY = rtorrent_directory
        mylar.RTORRENT_LABEL = rtorrent_label
        mylar.RTORRENT_STARTONLOAD = int(rtorrent_startonload)
        mylar.TRANSMISSION_HOST = transmission_host
        mylar.TRANSMISSION_USERNAME = transmission_username
        mylar.TRANSMISSION_PASSWORD = transmission_password
        mylar.TRANSMISSION_DIRECTORY = transmission_directory
        mylar.DELUGE_HOST = deluge_host
        mylar.DELUGE_USERNAME = deluge_username
        mylar.DELUGE_PASSWORD = deluge_password
        mylar.DELUGE_LABEL = deluge_label
        mylar.ENABLE_TORRENT_SEARCH = int(enable_torrent_search)
        mylar.ENABLE_TPSE = int(enable_tpse)
        mylar.ENABLE_32P = int(enable_32p)
        mylar.MODE_32P = int(mode_32p)
        mylar.RSSFEED_32P = rssfeed_32p
        mylar.PASSKEY_32P = passkey_32p
        mylar.USERNAME_32P = username_32p
        mylar.PASSWORD_32P = password_32p
        mylar.SNATCHEDTORRENT_NOTIFY = int(snatchedtorrent_notify)
        mylar.PREFERRED_QUALITY = int(preferred_quality)
        mylar.MOVE_FILES = move_files
        mylar.RENAME_FILES = rename_files
        mylar.REPLACE_SPACES = replace_spaces
        mylar.REPLACE_CHAR = replace_char
        mylar.ZERO_LEVEL = zero_level
        mylar.ZERO_LEVEL_N = zero_level_n
        mylar.ADD_TO_CSV = add_to_csv
        mylar.CVINFO = cvinfo
        mylar.LOWERCASE_FILENAMES = lowercase_filenames
        mylar.SYNO_FIX = syno_fix
        mylar.PROWL_ENABLED = prowl_enabled
        mylar.PROWL_ONSNATCH = prowl_onsnatch
        mylar.PROWL_KEYS = prowl_keys
        mylar.PROWL_PRIORITY = prowl_priority
        mylar.NMA_ENABLED = nma_enabled
        mylar.NMA_APIKEY = nma_apikey
        mylar.NMA_PRIORITY = nma_priority
        mylar.NMA_ONSNATCH = nma_onsnatch
        mylar.PUSHOVER_ENABLED = pushover_enabled
        mylar.PUSHOVER_APIKEY = pushover_apikey
        mylar.PUSHOVER_USERKEY = pushover_userkey
        mylar.PUSHOVER_PRIORITY = pushover_priority
        mylar.PUSHOVER_ONSNATCH = pushover_onsnatch
        mylar.BOXCAR_ENABLED = boxcar_enabled
        mylar.BOXCAR_ONSNATCH = boxcar_onsnatch
        mylar.BOXCAR_TOKEN = boxcar_token
        mylar.PUSHBULLET_ENABLED = pushbullet_enabled
        mylar.PUSHBULLET_APIKEY = pushbullet_apikey
        mylar.PUSHBULLET_DEVICEID = pushbullet_deviceid
        mylar.PUSHBULLET_ONSNATCH = pushbullet_onsnatch
        mylar.TELEGRAM_ENABLED = telegram_enabled
        mylar.TELEGRAM_TOKEN = telegram_token
        mylar.TELEGRAM_USERID = telegram_userid
        mylar.TELEGRAM_ONSNATCH = telegram_onsnatch
        mylar.USE_MINSIZE = use_minsize
        mylar.MINSIZE = minsize
        mylar.USE_MAXSIZE = use_maxsize
        mylar.MAXSIZE = maxsize
        if folder_format.startswith('/'):
            folder_format = re.sub('/', '', folder_format).strip()
        mylar.FOLDER_FORMAT = folder_format
        mylar.FILE_FORMAT = file_format
        mylar.DESTINATION_DIR = destination_dir
        mylar.CREATE_FOLDERS = create_folders
        mylar.AUTOWANT_ALL = autowant_all
        mylar.AUTOWANT_UPCOMING = autowant_upcoming
        mylar.COMIC_COVER_LOCAL = comic_cover_local
        mylar.INTERFACE = interface
        mylar.DUPECONSTRAINT = dupeconstraint
        mylar.DDUMP = ddump
        mylar.DUPLICATE_DUMP = duplicate_dump
        mylar.ENABLE_EXTRA_SCRIPTS = enable_extra_scripts
        mylar.EXTRA_SCRIPTS = extra_scripts
        mylar.ENABLE_PRE_SCRIPTS = enable_pre_scripts
        mylar.POST_PROCESSING = post_processing
        mylar.FILE_OPTS = file_opts
        mylar.PRE_SCRIPTS = pre_scripts
        mylar.ENABLE_META = enable_meta
        mylar.CBR2CBZ_ONLY = cbr2cbz_only
        mylar.CMTAGGER_PATH = cmtagger_path
        mylar.CT_TAG_CR = ct_tag_cr
        mylar.CT_TAG_CBL = ct_tag_cbl
        mylar.CT_CBZ_OVERWRITE = ct_cbz_overwrite
        mylar.UNRAR_CMD = unrar_cmd
        mylar.FAILED_DOWNLOAD_HANDLING = failed_download_handling
        mylar.FAILED_AUTO = failed_auto
        mylar.LOG_DIR = log_dir
        mylar.LOG_LEVEL = log_level
        mylar.ENFORCE_PERMS = enforce_perms
        mylar.CHMOD_DIR = chmod_dir
        mylar.CHMOD_FILE = chmod_file
        mylar.CHOWNER = chowner
        mylar.CHGROUP = chgroup
        # Handle the variable config options. Note - keys with False values aren't getting passed

        mylar.EXTRA_NEWZNABS = []
        #changing this for simplicty - adding all newznabs into extra_newznabs
        if newznab_host is not None:
            #this
            mylar.EXTRA_NEWZNABS.append((newznab_name, helpers.clean_url(newznab_host), newznab_verify, newznab_apikey, newznab_uid, int(newznab_enabled)))

        for kwarg in kwargs:
            if kwarg.startswith('newznab_name'):
                newznab_number = kwarg[12:]
                newznab_name = kwargs['newznab_name' + newznab_number]
                if newznab_name == "":
                    newznab_name = kwargs['newznab_host' + newznab_number]
                    if newznab_name == "":
                        logger.fdebug('Blank newznab provider has been entered - removing.')
                        continue
                newznab_host = helpers.clean_url(kwargs['newznab_host' + newznab_number])
                try:
                    newznab_verify = kwargs['newznab_verify' + newznab_number]
                except:
                    newznab_verify = 0
                newznab_api = kwargs['newznab_api' + newznab_number]
                newznab_uid = kwargs['newznab_uid' + newznab_number]
                try:
                    newznab_enabled = int(kwargs['newznab_enabled' + newznab_number])
                except KeyError:
                    newznab_enabled = 0

                mylar.EXTRA_NEWZNABS.append((newznab_name, newznab_host, newznab_verify, newznab_api, newznab_uid, newznab_enabled))

        # Sanity checking
        if mylar.COMICVINE_API == 'None' or mylar.COMICVINE_API == '' or mylar.COMICVINE_API == mylar.DEFAULT_CVAPI:
            logger.info('Personal Comicvine API key not provided. This will severely impact the usage of Mylar - you have been warned.')
            mylar.COMICVINE_API = None

        if mylar.SEARCH_INTERVAL < 360:
            logger.info("Search interval too low. Resetting to 6 hour minimum")
            mylar.SEARCH_INTERVAL = 360

        if mylar.SEARCH_DELAY < 1:
            logger.info("Minimum search delay set for 1 minute to avoid hammering.")
            mylar.SEARCH_DELAY = 1

        if mylar.RSS_CHECKINTERVAL < 20:
            logger.info("Minimum RSS Interval Check delay set for 20 minutes to avoid hammering.")
            mylar.RSS_CHECKINTERVAL = 20

        if not helpers.is_number(mylar.CHMOD_DIR):
            logger.info("CHMOD Directory value is not a valid numeric - please correct. Defaulting to 0777")
            mylar.CHMOD_DIR = '0777'

        if not helpers.is_number(mylar.CHMOD_FILE):
            logger.info("CHMOD File value is not a valid numeric - please correct. Defaulting to 0660")
            mylar.CHMOD_FILE = '0660'

        if mylar.SAB_HOST.endswith('/'):
            logger.info("Auto-correcting trailing slash in SABnzbd url (not required)")
            mylar.SAB_HOST = mylar.SAB_HOST[:-1]

        if mylar.FILE_OPTS is None:
            mylar.FILE_OPTS = 'move'

        if any([mylar.FILE_OPTS == 'hardlink', mylar.FILE_OPTS == 'softlink']):
            #we can't have metatagging enabled with hard/soft linking. Forcibly disable it here just in case it's set on load.
            mylar.ENABLE_META = 0

        if mylar.ENABLE_META:
            #force it to use comictagger in lib vs. outside in order to ensure 1/api second CV rate limit isn't broken.
            logger.fdebug("ComicTagger Path enforced to use local library : " + mylar.PROG_DIR)
            mylar.CMTAGGER_PATH = mylar.PROG_DIR

        #legacy support of older config - reload into old values for consistency.
        if mylar.NZB_DOWNLOADER == 0: mylar.USE_SABNZBD = True
        elif mylar.NZB_DOWNLOADER == 1: mylar.USE_NZBGET = True
        elif mylar.NZB_DOWNLOADER == 2: mylar.USE_BLACKHOLE = True

        if mylar.TORRENT_DOWNLOADER == 0:
            mylar.USE_WATCHDIR = True
        elif mylar.TORRENT_DOWNLOADER == 1:
            mylar.USE_UTORRENT = True
            mylar.USE_WATCHDIR = False
        elif mylar.TORRENT_DOWNLOADER == 2:
            mylar.USE_RTORRENT = True
            mylar.USE_WATCHDIR = False
        elif mylar.TORRENT_DOWNLOADER == 3:
            mylar.USE_TRANSMISSION = True
            mylar.USE_WATCHDIR = False

        # Write the config
        mylar.config_write()

        #raise cherrypy.HTTPRedirect("config")

    configUpdate.exposed = True

    def SABtest(self):
        sab_host = mylar.SAB_HOST
        sab_username = mylar.SAB_USERNAME
        sab_password = mylar.SAB_PASSWORD
        sab_apikey = mylar.SAB_APIKEY
        logger.fdebug('testing SABnzbd connection')
        logger.fdebug('sabhost: ' + str(sab_host))
        logger.fdebug('sab_username: ' + str(sab_username))
        logger.fdebug('sab_password: ' + str(sab_password))
        logger.fdebug('sab_apikey: ' + str(sab_apikey))
        if mylar.USE_SABNZBD:
            import requests
            from xml.dom.minidom import parseString, Element

            #if user/pass given, we can auto-fill the API ;)
            if sab_username is None or sab_password is None:
                logger.error('No Username / Password provided for SABnzbd credentials. Unable to test API key')
                return "Invalid Username/Password provided"
            logger.fdebug('testing connection to SABnzbd @ ' + sab_host)
            if sab_host.endswith('/'):
                sabhost = sab_host
            else:
                sabhost = sab_host + '/'

            querysab = sabhost + 'api'
            payload = {'mode':    'get_config',
                       'section': 'misc',
                       'output':  'xml',
                       'apikey':   sab_apikey}

            if sabhost.startswith('https'):
                verify = True
            else:
                verify = False

            try:
                r = requests.get(querysab, params=payload, verify=verify)
            except Exception, e:
                logger.warn('Error fetching data from %s: %s' % (sab_host, e))
                if requests.exceptions.SSLError:
                    logger.warn('Cannot verify ssl certificate. Attempting to authenticate with no ssl-certificate verification.')
                    try:
                        from requests.packages.urllib3 import disable_warnings
                        disable_warnings()
                    except:
                        logger.warn('Unable to disable https warnings. Expect some spam if using https nzb providers.')

                    verify = False

                    try:
                        r = requests.get(querysab, params=payload, verify=verify)
                    except Exception, e:
                        logger.warn('Error fetching data from %s: %s' % (sab_host, e))
                        return 'Unable to retrieve data from SABnzbd'
                else:
                    return 'Unable to retrieve data from SABnzbd'


            logger.info('status code: ' + str(r.status_code))

            if str(r.status_code) != '200':
                logger.warn('Unable to properly query SABnzbd @' + sabhost + ' [Status Code returned: ' + str(r.status_code) + ']')
                data = False
            else:
                data = r.content

            if data:
                dom = parseString(data)
            else:
                return 'Unable to reach SABnzbd'

            try:
                if dom.getElementsByTagName('status')[0].firstChild.wholeText == 'True':
                    q_sabhost = dom.getElementsByTagName('host')[0].firstChild.wholeText
                    q_nzbkey = dom.getElementsByTagName('nzb_key')[0].firstChild.wholeText
                    q_apikey = dom.getElementsByTagName('api_key')[0].firstChild.wholeText
                else:
                    raise ValueError
            except:
                errorm = dom.getElementsByTagName('error')[0].firstChild.wholeText
                logger.error(u"Error detected attempting to retrieve SAB data using FULL APIKey: " + errorm)
                if errorm == 'API Key Incorrect':
                    logger.fdebug('You may have given me just the right amount of power (NZBKey), will test SABnzbd against the NZBkey now')
                    querysab = sabhost + 'api'
                    payload = {'mode':    'addurl',
                               'name':    'http://www.example.com/example.nzb',
                               'nzbname': 'NiceName',
                               'output':  'xml',
                               'apikey':   sab_apikey}
                    try:
                        r = requests.get(querysab, params=payload, verify=verify)
                    except Exception, e:
                        logger.warn('Error fetching data from %s: %s' % (sab_host, e))
                        return 'Unable to retrieve data from SABnzbd'

                    dom = parseString(r.content)
                    qdata = dom.getElementsByTagName('status')[0].firstChild.wholeText

                    if str(qdata) == 'True':
                        q_nzbkey = mylar.SAB_APIKEY
                        q_apikey = None
                        qd = True
                    else:
                        qerror = dom.getElementsByTagName('error')[0].firstChild.wholeText
                        logger.error(str(qerror) + ' - check that the API (NZBkey) is correct, use the auto-detect option AND/OR check host:port settings')
                        qd = False

                if qd == False: return "Invalid APIKey provided."

            #test which apikey provided
            if q_nzbkey != sab_apikey:
                if q_apikey != sab_apikey:
                    logger.error('APIKey provided does not match with SABnzbd')
                    return "Invalid APIKey provided"
                else:
                    logger.info('APIKey provided is FULL APIKey which is too much power - changing to NZBKey')
                    mylar.SAB_APIKEY = q_nzbkey
                    mylar.config_write()
                    logger.info('Succcessfully changed to NZBKey. Thanks for shopping S-MART!')
            else:
                logger.info('APIKey provided is NZBKey which is the correct key.')

            logger.info('Connection to SABnzbd tested sucessfully')
            return "Successfully verified APIkey"
        else:
            logger.error('You do not have anything stated for SAB Host. Please correct and try again.')
            return "Invalid SABnzbd host specified"
    SABtest.exposed = True

    def shutdown(self):
        mylar.SIGNAL = 'shutdown'
        message = 'Shutting Down...'
        return serve_template(templatename="shutdown.html", title="Shutting Down", message=message, timer=15)
        return page

    shutdown.exposed = True

    def restart(self):
        mylar.SIGNAL = 'restart'
        message = 'Restarting...'
        return serve_template(templatename="shutdown.html", title="Restarting", message=message, timer=30)
    restart.exposed = True

    def update(self):
        mylar.SIGNAL = 'update'
        message = 'Updating...<br/><small>Main screen will appear in 60s</small>'
        return serve_template(templatename="shutdown.html", title="Updating", message=message, timer=30)
    update.exposed = True

    def getInfo(self, ComicID=None, IssueID=None):

        from mylar import cache
        info_dict = cache.getInfo(ComicID, IssueID)

        return simplejson.dumps(info_dict)

    getInfo.exposed = True

    def getComicArtwork(self, ComicID=None, imageURL=None):

        from mylar import cache
        logger.info(u"Retrieving image for : " + comicID)
        return cache.getArtwork(ComicID, imageURL)

    getComicArtwork.exposed = True

    def findsabAPI(self):
        import sabparse
        sabapi = sabparse.sabnzbd()
        logger.info('SAB NZBKey found as : ' + str(sabapi) + '. You still have to save the config to retain this setting.')
        mylar.SAB_APIKEY = sabapi
        return sabapi

    findsabAPI.exposed = True

    def generateAPI(self):

        import hashlib, random

        apikey = hashlib.sha224(str(random.getrandbits(256))).hexdigest()[0:32]
        logger.info("New API generated")
        mylar.API_KEY = apikey
        return apikey

    generateAPI.exposed = True

    def api(self, *args, **kwargs):

        from mylar.api import Api

        a = Api()

        a.checkParams(*args, **kwargs)

        data = a.fetchData()

        return data

    api.exposed = True

    def downloadthis(self, pathfile=None):
        #pathfile should be escaped via the |u tag from within the html call already.
        logger.fdebug('filepath to retrieve file from is : ' + pathfile)
        from cherrypy.lib.static import serve_download
        return serve_download(pathfile)

    downloadthis.exposed = True

    def IssueInfo(self, filelocation, comicname=None, issue=None, date=None, title=None):
        filelocation = filelocation.encode('ASCII')
        filelocation = urllib.unquote_plus(filelocation).decode('utf8')
        issuedetails = helpers.IssueDetails(filelocation)
        if issuedetails:
            issueinfo = '<table width="500"><tr><td>'
            issueinfo += '<img style="float: left; padding-right: 10px" src=' + issuedetails[0]['IssueImage'] + ' height="400" width="263">'
            seriestitle = issuedetails[0]['series']
            if any([seriestitle == 'None', seriestitle is None]):
                seriestitle = comicname

            issuenumber = issuedetails[0]['issue_number']
            if any([issuenumber == 'None', issuenumber is None]):
                issuenumber = issue

            issuetitle = issuedetails[0]['title']
            if any([issuetitle == 'None', issuetitle is None]):
                issuetitle = title

            issueinfo += '<h1><center><b>' + seriestitle + '</br>[#' + issuenumber + ']</b></center></h1>'
            issueinfo += '<center>"' + issuetitle + '"</center></br>'
            issueinfo += '</br><p class="alignleft">' + str(issuedetails[0]['pagecount']) + ' pages</p>'
            if all([issuedetails[0]['day'] is None, issuedetails[0]['month'] is None, issuedetails[0]['year'] is None]):
                issueinfo += '<p class="alignright">(' + str(date) + ')</p></br>'
            else:
                issueinfo += '<p class="alignright">(' + str(issuedetails[0]['year']) + '-' + str(issuedetails[0]['month']) + '-' + str(issuedetails[0]['day']) + ')</p></br>'
            if not any([issuedetails[0]['writer'] == 'None', issuedetails[0]['writer'] is None]):
                issueinfo += 'Writer: ' + issuedetails[0]['writer'] + '</br>'
            if not any([issuedetails[0]['penciller'] == 'None', issuedetails[0]['penciller'] is None]):
                issueinfo += 'Penciller: ' + issuedetails[0]['penciller'] + '</br>'
            if not any([issuedetails[0]['inker'] == 'None', issuedetails[0]['inker'] is None]):
                issueinfo += 'Inker: ' + issuedetails[0]['inker'] + '</br>'
            if not any([issuedetails[0]['colorist'] == 'None', issuedetails[0]['colorist'] is None]):
                issueinfo += 'Colorist: ' + issuedetails[0]['colorist'] + '</br>'
            if not any([issuedetails[0]['letterer'] == 'None', issuedetails[0]['letterer'] is None]):
                issueinfo += 'Letterer: ' + issuedetails[0]['letterer'] + '</br>'
            if not any([issuedetails[0]['editor'] == 'None', issuedetails[0]['editor'] is None]):
                issueinfo += 'Editor: ' + issuedetails[0]['editor'] + '</br>'
            issueinfo += '</td></tr>'
            #issueinfo += '<img src="interfaces/default/images/rename.png" height="25" width="25"></td></tr>'
            issuesumm = None
            if all([issuedetails[0]['summary'] == 'None', issuedetails[0]['summary'] is None]):
                issuesumm = 'No summary available within metatagging.'
            else:
                if len(issuedetails[0]['summary']) > 1000:
                    issuesumm = issuedetails[0]['summary'][:1000] + '...'
                else:
                    issuesumm = issuedetails[0]['summary']
            issueinfo += '<tr><td>Summary: ' + issuesumm + '</br></td></tr>'
            issueinfo += '<tr><td><center>' + os.path.split(filelocation)[1] + '</center>'
            issueinfo += '</td></tr></table>'

        else:
            ErrorPNG = 'interfaces/default/images/symbol_exclamation.png'
            issueinfo = '<table width="300"><tr><td>'
            issueinfo += '<img style="float: left; padding-right: 10px" src=' + ErrorPNG + ' height="128" width="128">'
            issueinfo += '<h1><center><b>ERROR</b></center></h1></br>'
            issueinfo += '<center>Unable to retrieve metadata from within cbz file</center></br>'
            issueinfo += '<center>Maybe you should try and tag the file again?</center></br>'
            issueinfo += '<tr><td><center>' + os.path.split(filelocation)[1] + '</center>'
            issueinfo += '</td></tr></table>'

        return issueinfo

    IssueInfo.exposed = True

    def manual_metatag(self, dirName, issueid, filename, comicid, comversion, seriesyear=None):
        module = '[MANUAL META-TAGGING]'
        try:
            import cmtagmylar
            if mylar.CMTAG_START_YEAR_AS_VOLUME:
                if all([seriesyear is not None, seriesyear != 'None']):
                    vol_label = seriesyear
                else:
                    logger.warn('Cannot populate the year for the series for some reason. Dropping down to numeric volume label.')
                    vol_label = comversion
            else:
                vol_label = comversion

            metaresponse = cmtagmylar.run(dirName, issueid=issueid, filename=filename, comversion=vol_label, manualmeta=True)
        except ImportError:
            logger.warn(module + ' comictaggerlib not found on system. Ensure the ENTIRE lib directory is located within mylar/lib/comictaggerlib/ directory.')
            metaresponse = "fail"

        if metaresponse == "fail":
            logger.fdebug(module + ' Unable to write metadata successfully - check mylar.log file.')
            return
        elif metaresponse == "unrar error":
            logger.error(module + ' This is a corrupt archive - whether CRC errors or it is incomplete. Marking as BAD, and retrying a different copy.')
            return
            #launch failed download handling here.
        else:
            dst = os.path.join(dirName, os.path.split(metaresponse)[1])
            shutil.move(metaresponse, dst)
            cache_dir = os.path.split(metaresponse)[0]
            logger.info(module + ' Sucessfully wrote metadata to .cbz (' + os.path.split(metaresponse)[1] + ') - Continuing..')
            if not os.listdir(cache_dir):
                logger.fdebug(module + ' Tidying up. Deleting temporary cache directory : ' + cache_dir)
                shutil.rmtree(cache_dir)
            else:
                logger.fdebug('Failed to remove temporary directory: ' + cache_dir)

        updater.forceRescan(comicid)

    manual_metatag.exposed = True

    def group_metatag(self, ComicID, dirName=None):
        myDB = db.DBConnection()
        cinfo = myDB.selectone('SELECT ComicLocation, ComicVersion, ComicYear, ComicName FROM comics WHERE ComicID=?', [ComicID]).fetchone()
        groupinfo = myDB.select('SELECT * FROM issues WHERE ComicID=? and Location is not NULL', [ComicID])
        if groupinfo is None:
            logger.warn('No issues physically exist within the series directory for me to (re)-tag.')
            return
        if dirName is None:
            meta_dir = cinfo['ComicLocation']
        else:
            meta_dir = dirName
        for ginfo in groupinfo:
            #if multiple_dest_dirs is in effect, metadir will be pointing to the wrong location and cause a 'Unable to create temporary cache location' error message
            self.manual_metatag(meta_dir, ginfo['IssueID'], os.path.join(meta_dir, ginfo['Location']), ComicID, comversion=cinfo['ComicVersion'], seriesyear=cinfo['ComicYear'])
        logger.info('[SERIES-METATAGGER][' + cinfo['ComicName'] + ' (' + cinfo['ComicYear'] + ')] Finished doing a complete series (re)tagging of metadata.')
    group_metatag.exposed = True

    def CreateFolders(self, createfolders=None):
        if createfolders:
            mylar.CREATE_FOLDERS = int(createfolders)
            mylar.config_write()

    CreateFolders.exposed = True

    def getPushbulletDevices(self, api=None):
        notifythis = notifiers.pushbullet
        result = notifythis.get_devices(api)
        if result:
            return result
        else:
            return 'Error sending Pushbullet notifications.'
    getPushbulletDevices.exposed = True

    def syncfiles(self):
        #3 status' exist for the readlist.
        # Added (Not Read) - Issue is added to the readlist and is awaiting to be 'sent' to your reading client.
        # Read - Issue has been read
        # Not Read - Issue has been downloaded to your reading client after the syncfiles has taken place.
        read = readinglist.Readinglist()
        threading.Thread(target=read.syncreading).start()
    syncfiles.exposed = True

    def search_32p(self, search=None):
        return mylar.rsscheck.torrents(pickfeed='4', seriesname=search)
    search_32p.exposed = True

    def testNMA(self):
        nma = notifiers.NMA()
        result = nma.test_notify()
        if result == True:
            return "Successfully sent NMA test -  check to make sure it worked"
        else:
            return "Error sending test message to NMA"
    testNMA.exposed = True

    def testprowl(self):
        prowl = notifiers.prowl()
        result = prowl.test_notify()
        if result:
            return "Successfully sent Prowl test -  check to make sure it worked"
        else:
            return "Error sending test message to Prowl"
    testprowl.exposed = True

    def testboxcar(self):
        boxcar = notifiers.boxcar()
        result = boxcar.test_notify()
        if result:
            return "Successfully sent Boxcar test -  check to make sure it worked"
        else:
            return "Error sending test message to Boxcar"
    testboxcar.exposed = True

    def testpushover(self):
        pushover = notifiers.PUSHOVER()
        result = pushover.test_notify()
        if result == True:
            return "Successfully sent PushOver test -  check to make sure it worked"
        else:
            return "Error sending test message to Pushover"
    testpushover.exposed = True

    def testpushbullet(self):
        pushbullet = notifiers.PUSHBULLET()
        result = pushbullet.test_notify()
        if result == True:
            return "Successfully sent Pushbullet test -  check to make sure it worked"
        else:
            return "Error sending test message to Pushbullet"
    testpushbullet.exposed = True

    def testtelegram(self):
        telegram = notifiers.TELEGRAM()
        result = telegram.test_notify()
        if result == True:
            return "Successfully sent Telegram test -  check to make sure it worked"
        else:
            return "Error sending test message to Telegram"
    testtelegram.exposed = True

    def orderThis(self, **kwargs):
        logger.info('here')
        return
    orderThis.exposed = True

    def torrentit(self, torrent_hash):
        import test
        #import lib.torrent.libs.rtorrent as rTorrent
        from base64 import b16encode, b32decode
        #torrent_hash  # Hash of the torrent
        logger.fdebug("Working on torrent: " + torrent_hash)

        if len(torrent_hash) == 32:
           torrent_hash = b16encode(b32decode(torrent_hash))

        if not len(torrent_hash) == 40:
           logger.error("Torrent hash is missing, or an invalid hash value has been passed")
           return
        else:
            rp = test.RTorrent()
            torrent_info = rp.main(torrent_hash, check=True)

        if torrent_info:
            torrent_name = torrent_info['name']
            torrent_info['filesize'] = helpers.human_size(torrent_info['total_filesize'])
            torrent_info['download'] = helpers.human_size(torrent_info['download_total'])
            torrent_info['upload'] = helpers.human_size(torrent_info['upload_total'])
            torrent_info['seedtime'] = helpers.humanize_time(amount=int(time.time()) - torrent_info['time_started'])

            logger.info("Client: %s", mylar.RTORRENT_HOST)
            logger.info("Directory: %s", torrent_info['folder'])
            logger.info("Name: %s", torrent_info['name'])
            logger.info("Hash: %s", torrent_info['hash'])
            logger.info("FileSize: %s", torrent_info['filesize'])
            logger.info("Completed: %s", torrent_info['completed'])
            logger.info("Downloaded: %s", torrent_info['download'])
            logger.info("Uploaded: %s", torrent_info['upload'])
            logger.info("Ratio: %s", torrent_info['ratio'])
            logger.info("Seeding Time: %s", torrent_info['seedtime'])

            if torrent_info['label']:
                logger.info("Torrent Label: %s", torrent_info['label'])

            ti = '<table><tr><td>'
            ti += '<center><b>' + torrent_name + '</b></center></br>'
            ti += '<center>' + torrent_info['hash'] + '</center>'
            ti += '<tr><td><center>Filesize: ' + torrent_info['filesize'] + '</center></td></tr>'
            ti += '<tr><td><center>' + torrent_info['download'] + ' DOWN / ' + torrent_info['upload'] + ' UP</center></td></tr>'
            ti += '<tr><td><center>Ratio: ' + str(torrent_info['ratio']) + '</center></td></tr>'
            ti += '<tr><td><center>Seedtime: ' + torrent_info['seedtime'] + '</center></td</tr>'
            ti += '</table>'
        else:
            torrent_name = 'Not Found'
            ti = 'Torrent not found (' + str(torrent_hash)
        return ti

    torrentit.exposed = True

    def get_the_hash(self, filepath):
        import hashlib, StringIO
        import rtorrent.lib.bencode as bencode

        # Open torrent file
        torrent_file = open(os.path.join('/home/hero/mylar/cache', filepath), "rb")
        metainfo = bencode.decode(torrent_file.read())
        info = metainfo['info']
        thehash = hashlib.sha1(bencode.encode(info)).hexdigest().upper()
        logger.info('Hash: ' + thehash)

    get_the_hash.exposed = True

    def test_32p(self):
        import auth32p
        p = auth32p.info32p(test=True)
        rtnvalues = p.authenticate()
        logger.info('32p return values: ' + str(rtnvalues))
        return rtnvalues
    test_32p.exposed = True
