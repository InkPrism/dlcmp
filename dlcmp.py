#!/usr/bin/env python3

import argparse
import sys
import json
from pathlib import Path
import os
import shutil
import urllib
import urllib.request
import urllib.parse
import posixpath
import re
import zipfile

def getheader(resp, head):
	# Try to retrieve the specified header
	try:
		return resp.info()[head]
	except:
		return "-HeadNotFound-"

def log_failed(content, do_log):
	print(content)
	if do_log:
		from datetime import datetime
		with open(str(datetime.now().date()) + '_dlcmp_failed.txt', 'a') as f:
			f.write('(' + str(datetime.now().time()) + ') ' + content + '\n')
def req(url, ua_head):
	req = urllib.request.Request(url)
	req.add_header('User-Agent', ua_head)
	return req

def dl(manifest, do_log, user_agent, verbose):
	print('\n(' + str(manifest) + ')')
	print('rtfm...')
	# Concrete path
	manifestpath = Path(manifest)
	# Get the parent
	manifestparent = manifestpath.parent
	# Read the content of manifest
	manifestcontent = manifestpath.open().read()
	# Load json from manifestcontent
	manifestJson = json.loads(manifestcontent)

	# Path to minecraft dir
	minecraftPath = Path(manifestparent, "minecraft")
	overridePath = Path(manifestparent, manifestJson['overrides'])
	# Check, if override exists and if true, move it into minecraft
	if overridePath.exists():
		shutil.move(str(overridePath), str(minecraftPath))

	# Fancy counter
	currF = 1
	allF = len(manifestJson['files'])
	print(str(allF) + ' mods found.')

	print('Downloading files...')

	# The magic...
	for dependency in manifestJson['files']:
		# Set project and file URLs
		projecturl = 'http://minecraft.curseforge.com/mc-mods/' + str(dependency['projectID'])
		try:
			# We need a redirection
			projectresp = urllib.request.urlopen(req(projecturl, user_agent))
			projecturl = projectresp.geturl() # (e. g. https://minecraft.curseforge.com/mc-mods/74924 -> https://minecraft.curseforge.com/projects/mantle)
		except:
			log_failed('Received a 404: ' + projecturl, do_log)
			currF = currF + 1
			continue
		try:
			# Open file URL
			filepath = projecturl + '/files/' + str(dependency['fileID']) + '/download'
			projectresp = urllib.request.urlopen(req(filepath, user_agent))
		except:
			log_failed('Received a 404: ' + projecturl, do_log)
			currF = currF + 1
			continue
#		# Get fileName from header
#		filename = projectresp.info()['Content-Disposition']
		# Get filename
		getrd = projectresp.geturl()
		path = urllib.parse.urlsplit(getrd).path
		filename = posixpath.basename(path)
		filename = filename.replace('%20', ' ')
		# Retrieve and write file
		print('[' + str(currF) + '/' + str(allF) + '] ' + str(filename))
		# Get file size from header if verbose is true
		if verbose:
			print(getheader(projectresp, "Content-Length") + " bytes.")
		# If file is already exists, skip
		if os.path.isfile(str(minecraftPath / "mods" / filename)):
			print('SKIPPED')
		else:
			with open(str(minecraftPath / "mods" / filename), "wb") as mod:
				mod.write(projectresp.read())
		currF = currF + 1
	print('Catched \'em all!')
	return

def get_modpack(url, do_log, user_agent, verbose):
	print('\n(' + str(url) + ')')
	print('Starting download...')
	try:
		to_file = '/download'
		if url.endswith(to_file):
			to_file = ''
		# Retrieving modpack
		dl_mp = urllib.request.urlopen(req(url + to_file, user_agent))
		resp = dl_mp.read()
		# Get the name for the file by getting the redirect from '/download' to 'someting/something.extenshion'
		dl_mp = dl_mp.geturl()
		dl_mp = dl_mp.replace("%20", " ")
		filename = posixpath.basename(dl_mp)
		print('Downloading ' + filename)
	except:
		log_failed('Could not open ' + url, do_log)
		return
	try:
		with open(filename, "wb") as f:
			f.write(resp)
	except:
		log_failed('Unable to write data from ' + str(url) + ' to ' + str(filename), do_log)
		return
	# Create new dir for extracted files
	dirname = filename
	# Why wouldn't it but hey...
	if filename.endswith('.zip'):
		dirname = dirname[:-4]
	# If Dir already exist
	if os.path.isdir(str(Path(dirname))):
		print('Dir ' + str(dirname) + ' already exists.')
		print('To not go at risk of destroying data, the procedure will be stopped.')
		return
	# Create the Dir
	try:
		os.makedirs(str(Path(dirname)))
	except:
		log_failed('Unable to create ' + str(dirname), do_log)
		return
	try:
		# Unzip the retrieved file
		zip_ref = zipfile.ZipFile(filename, 'r')
		zip_ref.extractall(str(Path(dirname)))
		zip_ref.close()
	except:
		log_failed('Unable to extract files from ' + str(filename), do_log)
		return
	try:
		# Delete the retrieved file
		os.remove(filename)
	except:
		log_failed('Unable to remove ' + str(filename), do_log)
		return
	# And now go and download the files
	dl(Path(dirname, 'manifest.json'), do_log, user_agent, verbose)

def main():
	parser = argparse.ArgumentParser(description="dlcmp - download utility for curse mod packs")
	parser.add_argument("-d", help="download modpack file (e.g. 'https://minecraft.curseforge.com/projects/invasion/files/2447205')")
	parser.add_argument("-m", help="manifest.json file from unzipped pack")
	parser.add_argument("--ua", help="User-Agent String")
	parser.add_argument("-v", help="show verbose information", action='store_true')
	parser.add_argument("-l", help="log failed requests", action='store_true')
	parser.set_defaults(ua='Mozilla/5.0 (Windows NT 6.1; WOW64; rv:37.0) Gecko/20100101 Firefox/37.0')
	parser.set_defaults(v=False)
	parser.set_defaults(l=False)
	args, unknown = parser.parse_known_args()
	print('Log: ' + str(args.l))
	if not args.d == None:
		get_modpack(str(args.d), args.l, args.ua, args.v)
	if not args.m == None:
		if not os.path.isfile(args.m):
			print('No manifest found at %s' % args.m)
			return
		dl(args.m, args.l, args.ua, args.v)

if __name__ == '__main__':
	main()
