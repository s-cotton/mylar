#!/usr/bin/env python

import re
import os, errno
import sys
import zipfile
import rarfile
from PIL import Image
import StringIO

from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True

# Comic Folder form Command Line
# Replace with DB Calls in mylar proper
ComicPath = sys.argv[1]

# Acceptible image extensions to process
pic_extensions = ('.jpg','.png','.webp','.gif','.jpeg')

# Determine Current Path (should be mylar root) for cache folder use
current_path = os.path.dirname(os.path.realpath(__file__))

# Use a Dict for testing, mylar.CACHE_DIR for final
mylar = dict([
    ('CACHE_DIR', os.path.join(current_path,'cache/'))
]);

numcheck = re.compile('[0-9]{2,3}')
onecheck = re.compile('0{1,2}1')
altcheck = re.compile('0{2,3}[A-Z]?[. ]', re.I)
merged_quality='web_medium'

# Give me something to do!
if ComicPath is None:
    print 'No Comic provided for Issue Cover Extraction'
else:
    # Store legit archive files
    issuefiles = []
    
    for (dirpath,dirnames,filenames) in os.walk(ComicPath):
        for filename in filenames:
            if filename.endswith('.cbz') or filename.endswith('.cbr'):
                issuefiles.append( filename )
    
    # Process each issue archive file
    for rawfilename in sorted(issuefiles):
        print "Processing ",rawfilename,'...'
        # locate the file in the filesystem
        srclocation = os.path.join( ComicPath, rawfilename )
        # track total covers for temp file naming
        covercount = 0
        # Temp Storage for found cover images
        cover_filenames = []
        # filtered storage for cover images (remove fallback 001 if we have more than one found cover)
        final_cover_filenames = []
        loaded_archive = False

        try:
            if rawfilename.endswith('.cbz'):
                # Load up the zip
                issuefile = zipfile.ZipFile(srclocation)
            else :
                # Load up the rar
                issuefile = rarfile.RarFile(srclocation)
            loaded_archive = True
        except:
            print 'ERROR. Could not open ' + rawfilename + ' for cover extraction: ', sys.exc_info()

        if loaded_archive:
            # raw, all images in archive
            allimages = []
            # all images that have a page number pattern
            allimagesclean = []
            # Determine common part of filenames to remove possible number based names that wouold interfere with determining cover files
            for afile in issuefile.namelist():
                if afile.endswith(pic_extensions):
                    #print afile
                    allimages.append(afile)

            # No need to re-invent the wheel
            common_name = os.path.commonprefix(allimages)

            # Loop over images and determine if they have page numbers, hopefully stripping out the scene files
            for afile in allimages:
                afile_trimmed = afile.replace(common_name,"")
                #print "Checking ", afile_trimmed, numcheck.match(afile_trimmed)
                if numcheck.search(afile_trimmed) is not None:
                    allimagesclean.append(afile)

            common_name = os.path.commonprefix(allimagesclean)

            # Loop over all "valid" page number archived images
            for infile in allimagesclean:
                check_filename = infile.replace(common_name,"")
                filename,file_extension = os.path.splitext(check_filename)
                
                isCover = False
                
                # If our stripped down page number can be interpreted as a number, eval it as an integer (quickest way to get rid of 100 101 200 201 etc matches)
                if filename.isdigit():
                    if int(filename) == 0 or int(filename) == 1:
                        isCover = True
                # It's not a number, so look specifically for 2-3 zeros followed by a possible letter.  This would still fail to restrict to covers if you have more than 1000 pages, but any real number should
                # be caught by the isidigit call above
                else:
                    if altcheck.search(check_filename) is not None:
                        isCover = True

                if isCover:
                    cover_filenames.append(infile)

            print "Found ", len(cover_filenames)," raw covers..."

            # If we have more than one cover, get rid of the 001 fallbacks.  This may need to be updated to run through twice to ensure we havent hit
            # a situation where we have more than one 001 fallbacks and no 000 covers
            if len(cover_filenames) > 1:
                zero_found = False
                # Look for any covers whos page number matches the zero pattern
                for cover_filename in sorted(cover_filenames):
                    check_filename = cover_filename.replace(common_name,"")
                    filename,file_extension = os.path.splitext(check_filename)
                    if altcheck.search(check_filename) is not None:
                        zero_found = True

                if zero_found:
                    # since we have a zero, let's strip out the 01 001 pages
                    for cover_filename in sorted(cover_filenames):
                        check_filename = cover_filename.replace(common_name,"")
                        filename,file_extension = os.path.splitext(check_filename)
                        if not onecheck.search(check_filename):
                            final_cover_filenames.append(cover_filename)
                else:
                    # No zeros found, so we will just accept the 01 as the fallback
                    for cover_filename in sorted(cover_filenames):
                        final_cover_filenames.append(cover_filename)

            else:
                # Only one cover found, this would be the case for archives with no 00 named pages, so we have grabbed 01
                final_cover_filenames = cover_filenames

            print "Found ", len(final_cover_filenames)," covers..."

            if len(final_cover_filenames) > 0:

                # Final merged image created as a new image wide enough for all of the found covers
                final_image_path = os.path.join(mylar['CACHE_DIR'],'temp-cover-' + rawfilename + '.jpg')
                merged_image = Image.new('RGB', (len(final_cover_filenames) * 600,922));
                print "Merging ",len(final_cover_filenames)," covers: ",str(len(final_cover_filenames) * 600),"x",str(922),"..."

                # Extract each image from the archive
                for cover_filename in sorted(final_cover_filenames):
                    print 'Extracting cover: ', cover_filename
                    infile = issuefile.getinfo(cover_filename)
                    # Read the file in as a string buffer, saving us an unnecessary save
                    img = Image.open( StringIO.StringIO( issuefile.read(infile) ))
                    wpercent = (600/float(img.size[0]))
                    hsize = int((float(img.size[1])*float(wpercent)))
                    # resize to the max used on the site, 600 px wide
                    img = img.resize((600,hsize), Image.ANTIALIAS)
                    if( hsize > 922 ):
                        img = img.crop((0,0,600,922))
                    merged_image.paste( img, (covercount * 600,0));
                    covercount += 1
            
                merged_image.save(final_image_path, "JPEG", quality=merged_quality)