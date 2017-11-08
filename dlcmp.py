#!/usr/bin/env python3

from pathlib import Path
import os
import shutil
import urllib.request
import urllib.parse
import posixpath

def getheader(resp, head):
    # Try to retrieve the specified header
    try:
        return resp.info()[head]
    except:
        return "-HeadNotFound-"

def log_failed(content, log):
    print(content)
    if log is not None:
        try:
            with open(log, 'a') as f:
                f.write(content + '\n')
                f.close()
        except (OSError, FileNotFoundError) as e:
            pass

def req(url, ua_head):
    req = urllib.request.Request(url)
    req.add_header('User-Agent', ua_head)
    return req

def dl(manifest, log, user_agent, verbose, cache):
    import json
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
    # Check, if a cache path was given...
    if cache is not None:
        if os.path.isdir(cache):
            cachepath = Path(cache)
            cachedl = True
        else:
            print(str(cache) + " is no directory or cannot be accessed as such. Continuing without cache.")
            cachedl = False
    else:
        cachedl = False

    # The magic...
    for dependency in manifestJson['files']:
        if cachedl:
            targetdir = Path(cachepath, str(dependency['projectID']), str(dependency['fileID']))
            if os.path.isdir(targetdir):
                # targeted dir exists, getting the first (there should only be one... *knock on wood*.)
                targetfile = [f for f in targetdir.iterdir()]
                if len(targetfile) >= 1:
                    targetfile = targetfile[0]
                    shutil.copyfile(str(targetfile), str(minecraftPath / "mods" / targetfile.name))
                    currF += 1
                    continue
        # Set project URL
        projecturl = 'https://minecraft.curseforge.com/projects/' + str(dependency['projectID'])
        try:
            # Open file URL
            filepath = projecturl + '/files/' + str(dependency['fileID']) + '/download'
            projectresp = urllib.request.urlopen(req(filepath, user_agent))
        except urllib.error.HTTPError as e:
            log_failed(str(e.code) + ' - ' + projecturl, log)
            currF += 1
            continue
#        # Get fileName from header
#        filename = projectresp.info()['Content-Disposition']
        # Get filename
        getrd = projectresp.geturl()
        path = urllib.parse.urlsplit(getrd).path
        filename = posixpath.basename(path)
        filename = filename.replace('%20', ' ')
        # Retrieve and write file
        print('[' + str(currF) + '/' + str(allF) + '] ' + str(filename), end='')
        # Get file size from header if verbose is true
        if verbose:
            print(" - %s bytes" % getheader(projectresp, "Content-Length"), end="")
        # If file is already exists, skip
        if os.path.isfile(str(minecraftPath / "mods" / filename)):
            print(' - SKIPPED')
        else:
            with open(str(minecraftPath / "mods" / filename), "wb") as mod:
                mod.write(projectresp.read())
            # If a cache is used, add the file to it.
            if cachedl:
                targetcachepath = Path(cachepath, str(dependency['projectID']), str(dependency['fileID']))
                if os.path.exists(targetcachepath):
                    targetcachepath.mkdir(parents=True)
                shutil.copyfile(str(minecraftPath / "mods" / filename), str(cachepath / str(dependency['projectID']) / str(dependency['fileID']) / filename))
            print(" - Done")
        currF += 1
    print('Catched \'em all!')
    return

def get_modpack(url, log, user_agent, verbose, cache):
    import zipfile
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
    except urllib.error.HTTPError as e:
        log_failed(e + ' - ' + url, log)
        return
    try:
        with open(filename, "wb") as f:
            f.write(resp)
    except (OSError, IOError) as e:
        log_failed(e, log)
        log_failed('Unable to write data from ' + str(url) + ' to ' + str(filename), log)
        return
    # Create new dir for extracted files
    dirname = filename
    # Why wouldn't it but hey...
    if filename.endswith('.zip'):
        dirname = dirname[:-4]
    # If Dir already exist
    if os.path.isdir(str(Path(dirname))):
        log_failed('Dir ' + str(dirname) + ' already exists.', log)
        log_failed('To not go at risk of destroying data, the procedure will be stopped.', log)
        return
    # Create the Dir
    try:
        os.makedirs(str(Path(dirname)))
    except OSError as e:
        log_failed(e, log)
        log_failed('Unable to create ' + str(dirname), log)
        return
    try:
        # Unzip the retrieved file
        zip_ref = zipfile.ZipFile(filename, 'r')
        zip_ref.extractall(str(Path(dirname)))
        zip_ref.close()
    except FileNotFoundError as e:
        log_failed(e, log)
        return
    except zipfile.BadZipFile as e:
        log_failed(e, log)
        return
    except:
        log_failed('Unable to extract files from ' + str(filename), log)
        return
    try:
        # Delete the retrieved file
        os.remove(filename)
    except FileNotFoundError as e:
        log_failed(e, log)
        log_failed('Still attempting to read \'manifest.json\'', log)
    except OSError as e:
        log_failed(e, log)
        log_failed('Unable to remove ' + str(filename), log)
    # And now go and download the files
    dl(Path(dirname, 'manifest.json'), log, user_agent, verbose, cache)

def main():
    import argparse
    import re
    parser = argparse.ArgumentParser(description="dlcmp - download utility for curse mod packs")
    parser.add_argument("dest", metavar='destination', nargs='?', help="url or path (e.g. 'https://minecraft.curseforge.com/projects/invasion/files/2447205' or 'path/2/manifest.json')", default=None)
    parser.add_argument("--url", "--prefer-url", dest='url', help="positional argument will be handled as an URL", action='store_true', default=False)
    parser.add_argument("--path", "--prefer-path", dest='path', help="positional argument will be handled as a path", action='store_true', default=False)
    parser.add_argument("--ua", "--user-agent", metavar='user-agent-string', dest='useragent', help="User-Agent String", default='Mozilla/5.0 (Windows NT 6.1; WOW64; rv:37.0) Gecko/20100101 Firefox/37.0') # http://techblog.willshouse.com/2012/01/03/most-common-user-agents/
    parser.add_argument("-v", "--verbose", dest='verbose', help="show verbose information", action='store_true', default=False)
    parser.add_argument("-l", "--log", dest='log' , metavar='logfile', help="log failed requests", default=None)
    parser.add_argument("-c", "--cache", dest='cache', metavar='cachedir', help='path to cache directory')
    args, unknown = parser.parse_known_args()
    if args.verbose:
        print('Log: ' + str(args.log))
        print('User-Agent: ' + str(args.useragent))
    if args.dest == None:
        print('No positional argument found. Aborting.')
        return
    # Test, if it is a url (with bad regex) and not specified as path (or if it is specified as url)
    match = re.match(r'^(?:(?:http|ftp)s?://).*$', args.dest, re.IGNORECASE)
    if  match and not args.path or args.url:
        get_modpack(str(args.dest), args.log, args.useragent, args.verbose, args.cache)
    # Specified as path?
    else:
        if not os.path.isfile(args.dest):
            print('No manifest found at %s' % args.dest)
            return
        dl(args.dest, args.log, args.useragent, args.verbose, args.cache)

if __name__ == '__main__':
    main()
