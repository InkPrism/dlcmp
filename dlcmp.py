#!python3

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

def dl(manifest):
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
			projectresp = urllib.request.urlopen(projecturl)
			projecturl = projectresp.geturl()
		except:
			print('Received a 404: ' + projecturl)
			currF = currF + 1
			continue
		# Open file URL
		filepath = projecturl + '/files/' + str(dependency['fileID']) + '/download'
		projectresp = urllib.request.urlopen(filepath)
#		# Get fileName from header
#		filename = projectresp.info()['Content-Disposition']
		# Get filename
		getrd = projectresp.geturl()
		path = urllib.parse.urlsplit(getrd).path
		filename = posixpath.basename(path)
		filename = filename.replace('%20', ' ')
		# Retrieve and write file
		print('[' + str(currF) + '/' + str(allF) + '] ' + str(filename))
		# If file is already exists, skip
		if os.path.isfile(str(minecraftPath / "mods" / filename)):
			print('SKIPPED')
		else:
			with open(str(minecraftPath / "mods" / filename), "wb") as mod:
				mod.write(projectresp.read())
		currF = currF + 1
	print('Catched \'em all!')
	return

def get_modpack(url):
	print('\n(' + str(url) + ')')
	print('Starting download...')
	try:
		to_file = '/download'
		if url.endswith(to_file):
			to_file = ''
		# Retrieving modpack
		dl_mp = urllib.request.urlopen(url + to_file)
		resp = dl_mp.read()
		# Get the name for the file by getting the redirect from '/download' to 'someting/something.extenshion'
		dl_mp = dl_mp.geturl()
		dl_mp = dl_mp.replace("%20", " ")
		filename = posixpath.basename(dl_mp)
		print('Downloading ' + filename)
	except:
		print('Could not open ' + url)
		return
	try:
		with open(filename, "wb") as f:
			f.write(resp)
	except:
		print('Unable to write data from ' + str(url) + ' to ' + str(filename))
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
		print('Unable to create ' + str(dirname))
		return
	# Unzip the retrieved file
	zip_ref = zipfile.ZipFile(filename, 'r')
	zip_ref.extractall(str(Path(dirname)))
	zip_ref.close()
	# Delete the retrieved file
	os.remove(filename)
	# And now go and download the files
	dl(Path(dirname, 'manifest.json'))

def main():
	parser = argparse.ArgumentParser(description="dlcmp - download utility for curse mod packs")
	parser.add_argument("-d", help="download modpack file (e.g. 'https://minecraft.curseforge.com/projects/invasion/files/2447205')")
	parser.add_argument("-m", help="manifest.json file from unzipped pack")
	args, unknown = parser.parse_known_args()
	if not args.d == None:
		get_modpack(str(args.d))
	if not args.m == None:
		if not os.path.isfile(args.m):
			print('No manifest found at %s' % args.m)
			return
		dl(args.m)

if __name__ == '__main__':
	main()
