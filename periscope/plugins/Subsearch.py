# -*- coding: utf-8 -*-

#   This file is part of periscope.
#   Copyright (c) 2008-2011 Patrick Dessalle <patrick@dessalle.be>
#
#    periscope is free software; you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    periscope is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with periscope; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import zipfile, os, urllib2, urllib, logging, traceback, httplib
import urlparse
from bs4 import BeautifulSoup
import HTMLParser
import re

import SubtitleDatabase

SS_LANGUAGES = {"fi": "Finnish"}

class Subsearch(SubtitleDatabase.SubtitleDB):
	url = "http://subsearch.org/"
	site_name = "Subsearch"

	def __init__(self, config, cache_folder_path):
		super(Subsearch, self).__init__(SS_LANGUAGES)
		#http://subsearch.org/search/Arrow.S04E10.HDTV.x264-LOL/fi/4/0/0
		self.host = "http://subsearch.org"

	def process(self, filepath, langs):
		''' main method to call on the plugin, pass the filename and the wished 
		languages and it will query the subtitles source '''
		fname = self.getFileName(filepath)
		try:
			subs = self.query(fname, langs)
			if not subs and fname.rfind(".[") > 0:
				# Try to remove the [VTV] or [EZTV] at the end of the file
				teamless_filename = fname[0 : fname.rfind(".[")]
				subs = self.query(teamless_filename, langs)
				return subs
			else:
				return subs
		except Exception, e:
			logging.error("Error raised by plugin %s: %s" %(self.__class__.__name__, e))
			traceback.print_exc()
			return []
			
	def createFile(self, subtitle):
		'''pass the URL of the sub and the file it matches, will unzip it
		and return the path to the created file'''
		subpage = subtitle["page"]
		suburl = subtitle["link"]
		release = subtitle["release"]
		format = subtitle["format"]
		targetbasename = subtitle["targetfile"]
		page = urllib2.urlopen(subpage)
		soup = BeautifulSoup(page, "html.parser")

		srtbasefilename = release
		archivefilename = release + '.'+ format
		self.downloadFile(suburl, archivefilename)
		subtitlefilename = None
		
		subtitlefiles = []

		if zipfile.is_zipfile(archivefilename):
			logging.debug("Unzipping file " + archivefilename)
			zf = zipfile.ZipFile(archivefilename, "r")
			for el in zf.infolist():
				extension = el.orig_filename.rsplit(".", 1)[1]
				if extension in ("srt", "sub", "txt"):
					subtitlefilename = srtbasefilename + "." + extension
					#outfile = open(subtitlefilename, "wb")
					outfile = open(el.orig_filename, "wb")
					outfile.write(zf.read(el.orig_filename))
					outfile.flush()
					outfile.close()
					#subtitlefiles.append(subtitlefilename)
					subtitlefiles.append(el.orig_filename)
				else:
					logging.info("File %s does not seem to be valid " %el.orig_filename)
			# Deleting the zip file
			zf.close()
			#os.remove(archivefilename)
			#return subtitlefilename
		elif archivefilename.endswith('.rar'):
			logging.warn('Rar is not really supported yet. Trying to call unrar')
			import subprocess
			try :
				args = ['unrar', 'lb', archivefilename]
				output = subprocess.Popen(args, stdout=subprocess.PIPE).communicate()[0]
				logging.debug("----")
				logging.debug("output: %s" %output)
				logging.debug("----")
				for el in output.splitlines():
					logging.debug("Processing: %s" %el)
					extension = el.rsplit(".", 1)[1]
					if extension in ("srt", "sub"):
						args = ['unrar', 'e', archivefilename, el, os.path.dirname(archivefilename)]
						output2 = subprocess.Popen(args, stdout=subprocess.PIPE).communicate()[0]
						#tmpsubtitlefilename = os.path.join(os.path.dirname(archivefilename), el)
						#subtitlefilename = os.path.join(os.path.dirname(archivefilename), srtbasefilename+".fi."+extension)
						#if os.path.exists(tmpsubtitlefilename):
							# rename it to match the file
							# os.rename(tmpsubtitlefilename, subtitlefilename)
							# exit
						#os.remove(archivefilename)
						#return subtitlefilename
						subtitlefiles.append(el)
			except OSError, e:
			    logging.error("Execution failed: %s" %e)
			    return None

		else:
			logging.info("Unexpected file type (not zip nor rar) for %s" %archivefilename)
			return None

		targetpath = os.path.dirname(archivefilename)

		if os.path.exists(archivefilename):
			os.remove(archivefilename)

		filelist = []

		# Remove unnecessary filename parts
		for filename in subtitlefiles:
			extension = filename.rsplit(".", 1)[1]
			if filename.endswith(''.join(['SubFinland.org.', extension])):
				if os.path.exists(os.path.join(os.path.dirname(archivefilename), filename)):
					filename2 = ''.join([filename[0:-18], extension])
					os.rename(os.path.join(targetpath, filename), os.path.join(targetpath, filename2))
					logging.debug("Renaming %s to %s" %(filename, filename2))
					filename = filename2
			filelist.append(filename)

		subtitlefiles = []

		if len(filelist) == 0:
			logging.warn("No suitable subtitle file found.")
			exit()

		if len(filelist) > 1:
			# Try to find a matching subtitle
			match_found = 0
			removables = []
			matches = []
			for filename in filelist:
				if filename.rsplit(".", 1)[0] != srtbasefilename:
					removables.append(filename)
				else:
					match_found = 1
					matches.append(filename)
			if match_found == 1 and len(matches) > 0:
				for removable in removables:
					if os.path.exists(os.path.join(targetpath, removable)):
						os.remove(os.path.join(targetpath, removable))
				filelist = [matches[0]]

			# Did not find a perfect match, accept first file
			if len(filelist) > 1:
				for filename in filelist:
					if filename != filelist[0] and os.path.exists(os.path.join(targetpath, filename)):
						os.remove(os.path.join(targetpath, filename))
				filelist = [filelist[0]]

		# Rename to exact match
		if filelist[0] != srtbasefilename and os.path.exists(os.path.join(targetpath, filelist[0])):
			sourcefile = filelist[0]
			extension = sourcefile.rsplit(".", 1)[1]
			targetfile = ''.join([srtbasefilename, '.', extension])
			os.rename(os.path.join(targetpath, sourcefile), os.path.join(targetpath, targetfile))
			filelist[0] = targetfile
			logging.debug("Renamed %s to %s" %(sourcefile, targetfile))

		# Support stripping of year and force to match release
		if filelist[0].rsplit(".", 1)[0] != targetbasename and os.path.exists(os.path.join(targetpath, filelist[0])):
			sourcefile = filelist[0]
			extension = sourcefile.rsplit(".", 1)[1]
			targetfile = ''.join([targetbasename, '.', extension])
			os.rename(os.path.join(targetpath, sourcefile), os.path.join(targetpath, targetfile))
			filelist[0] = targetfile
			logging.debug("Forced %s to match with release %s" %(sourcefile, targetfile))			

		# Append language id to filename
		if not filelist[0].endswith(".fi." + extension) and os.path.exists(os.path.join(targetpath, filelist[0])):
			sourcefile = filelist[0]
			sourcefile_basename = sourcefile.rsplit(".", 1)[0]
			extension = sourcefile.rsplit(".", 1)[1]
			targetfile = ''.join([sourcefile_basename, '.fi.', extension])
			os.rename(os.path.join(targetpath, sourcefile), os.path.join(targetpath, targetfile))
			filelist[0] = targetfile
			logging.debug("Renamed %s to %s" %(sourcefile, targetfile))

		logging.debug("Extracted: %s" %filelist[0])
		return filelist[0]

	def query(self, token, langs=None):
		''' makes a query on subscene and returns info (link, lang) about found subtitles'''
		sublinks = []

		# Strip year from release name
		newtoken = re.sub(r"\b[0-9]{4}[\.]{1}\b", "", token).rstrip()
		
		if sum(c.isdigit() for c in newtoken) == 0:
			newtoken = token

		# Strip [eztv] and similar unnecessary parts of release name
		if newtoken.endswith("]"):
			newtoken = newtoken.rsplit("[", 1)[0]

		searchurl = "%s/search/%s/fi/4/0/0" %(self.host, urllib.quote(newtoken))
		logging.debug("dl'ing %s" %searchurl)
		page = urllib2.urlopen(searchurl)

		soup = BeautifulSoup(page, "html.parser")

		if len(soup("tr", {"style":"border: 3px double #ddd;background:#fffef9;height:35px;"})) == 0:
			logging.debug("No subtitles found - Trying alternative naming")
			dot_count = len(re.findall(".", newtoken))
			if dot_count > 1:
				alt_rels = []
				filename_leftover = newtoken.rsplit(".", 1)[0]
				alt_rel_number = filename_leftover.rsplit(".", 1)[1]
				alt_rel_seriename = filename_leftover.rsplit(".", 1)[0].replace(".", " ")
				alt_rel_src = newtoken.rsplit(".", 1)[1]
				alt_rel_season = "S"
				alt_rel_episode = "E"
				if len(re.findall("-", alt_rel_src)) == 0:
					alt_rels.append(alt_rel_src)
				else:
					alt_rels.append(alt_rel_src.rsplit("-", 1)[0])
					alt_rels.append(alt_rel_src.rsplit("-", 1)[1])
				if len(alt_rel_number) == 3:
					alt_rel_season = ''.join(['S0', alt_rel_number[0]])
					alt_rel_episode = ''.join(['E', alt_rel_number[1:3]])
				elif len(alt_rel_number) == 4:
					alt_rel_season = ''.join(['S', alt_rel_number[0:2]])
					alt_rel_episode = ''.join(['E', alt_rel_number[2:4]])
				else:
					logging.debug("Alternative naming failed.")
					return []

				newtoken = ''.join([alt_rel_seriename.title(), '.'])
				newtoken = ''.join([newtoken, alt_rel_season, alt_rel_episode])

				alt_rel_index = 0
				for alt_rel in alt_rels:
					alt_rel_index = alt_rel_index + 1
					if len(alt_rels) > 1 and alt_rel_index == len(alt_rels):
						newtoken = ''.join([newtoken, '.x264-', alt_rel.upper()])
					else:
						newtoken = ''.join([newtoken, '.', alt_rel.upper()])

				logging.debug("Generated alternative name: %s" %newtoken)

				searchurl = "%s/search/%s/fi/4/0/0" %(self.host, urllib.quote(newtoken))
				logging.debug("dl'ing %s" %searchurl)
				page = urllib2.urlopen(searchurl)
				soup = BeautifulSoup(page, "html.parser")

		for subs in soup("tr", {"style":"border: 3px double #ddd;background:#fffef9;height:35px;"}):
			sublink = subs.find("a")

			if str(sublink["href"]).startswith('http://www.imdb.com/'):
				logging.debug('skipping imdb link')
				sublink = sublink.findNext("a")

			page_link = sublink["href"]
			logging.debug("page link: %s" %page_link)

			source_link = str(sublink.findNext("a").contents[0])
			logging.debug("source link: %s" %source_link)

			release_names = sublink["onmouseover"]

			if str(release_names).startswith("Tip('") and str(release_names).endswith("')"):
				releasenames = release_names[5:-2]

			release_names = str(release_names).split('Releasename/other info:</b><br/>')[1]
			
			if str(release_names).startswith("<span style=margin-left:10px;>"):
				release_names = release_names[30:-9]

			release_names = str(release_names).split('<br />')

			logging.debug("Count of releases: %s" %str(len(release_names)))
			logging.debug("Releases: %s" %release_names)

			for release_name in release_names:

				result = {}
				result["release"] = release_name
				result["lang"] = "fi"
				result["page"] = page_link
				result["link"] = None
				result["targetfile"] = token

				release_stripped = re.sub(r"\b[0-9]{4}[\.]{1}\b", "", release_name).rstrip()

				if release_stripped.upper().startswith(newtoken.upper()) and source_link.upper() == 'SUBHEAVEN':

					download_link = urlparse.parse_qs(urlparse.urlparse(page_link).query)
					download_link = download_link['sid'][0]
					download_link = ''.join(['http://subheaven.org/download.php?sid=', download_link])
					result["format"] = "zip"
					result["link"] = download_link

				elif release_stripped.upper().startswith(newtoken.upper()) and source_link.upper() == 'SUBFINLAND':

					download_link = urlparse.parse_qs(urlparse.urlparse(page_link).query)
					download_link = download_link['sid'][0]
					download_link = ''.join(['http://subfinland.org/download.php?f=', download_link])
					result["format"] = "rar"
					result["link"] = download_link

				if not result["link"] == None:
					logging.debug("Download link: %s" %result["link"])
					sublinks.append(result)

		logging.debug("Results: %s" %sublinks)
		return sublinks
