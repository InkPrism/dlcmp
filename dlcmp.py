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
        return "-"


def report(content, silent, end=os.linesep):
    if not silent:
        print(content, end=end)


def log_failed(content, log, silent):
    report(content, silent)
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


def dl(manifest, log=None, user_agent="-", verbose=False, cache=None, silent=False):
    import json
    report('\n[*] ' + str(manifest), silent)
    report('rtfm...', silent)
    # Concrete path
    manifestpath = Path(manifest)
    # Get the parent
    manifestparent = manifestpath.parent
    # Read the content of manifest
    # Load json from manifestcontent
    manifestjson = json.loads(manifestpath.open().read())

    # Path to minecraft dir
    minecraftpath = Path(manifestparent, "minecraft")
    overridepath = Path(manifestparent, manifestjson['overrides'])
    # Check, if override exists and if true, move it into minecraft
    if overridepath.exists():
        shutil.move(str(overridepath), str(minecraftpath))
    # Check, if mods dir exists
    if not Path(minecraftpath, "mods").exists():
        os.mkdir(str(minecraftpath / "mods"))

    # Fancy counter
    currF = 1
    allF = len(manifestjson['files'])
    report(str(allF) + ' mods found.', silent)

    report('Downloading files...', silent)

    # Check, if a cache path was given...
    cachedl = False
    if cache is not None:
        if os.path.isdir(cache):
            cachepath = Path(cache)
            cachedl = True
        else:
            log_failed(str(cache) + " is no directory or cannot be accessed as such. Continuing without cache.", log, silent)

    # The magic...
    for dependency in manifestjson['files']:
        if cachedl:
            targetdir = Path(cachepath, str(dependency['projectID']), str(dependency['fileID']))
            if os.path.isdir(targetdir):
                # targeted dir exists, getting the first (there should only be one... *knock on wood*.)
                targetfile = [f for f in targetdir.iterdir()]
                if len(targetfile) >= 1:
                    targetfile = targetfile[0]
                    shutil.copyfile(str(targetfile), str(minecraftpath / "mods" / targetfile.name))
                    currF += 1
                    continue
        # Set project URL
        projecturl = 'https://minecraft.curseforge.com/projects/' + str(dependency['projectID'])
        try:
            # Open file URL
            filepath = projecturl + '/files/' + str(dependency['fileID']) + '/download'
            projectresp = urllib.request.urlopen(req(filepath, user_agent))
        except urllib.error.HTTPError as e:
            log_failed(str(e.code) + ' - ' + filepath, log, silent)
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
        report('[' + str(currF) + '/' + str(allF) + '] ' + str(filename), silent, end='')
        # Get file size from header if verbose is true
        if verbose:
            report(" - %s bytes" % getheader(projectresp, "Content-Length"), silent, end="")
        # If file is already exists, skip
        if os.path.isfile(str(minecraftpath / "mods" / filename)):
            report(' - SKIPPED', silent)
        else:
            with open(str(minecraftpath / "mods" / filename), "wb") as mod:
                mod.write(projectresp.read())
            # If a cache is used, add the file to it.
            if cachedl:
                targetcachepath = Path(cachepath, str(dependency['projectID']), str(dependency['fileID']))
                if os.path.exists(targetcachepath):
                    targetcachepath.mkdir(parents=True)
                shutil.copyfile(str(minecraftpath / "mods" / filename), str(cachepath / str(dependency['projectID']) / str(dependency['fileID']) / filename))
            report(" - Done", silent)
        currF += 1
    report('Catched \'em all!', silent)
    return


def get_modpack(url, log=None, user_agent="-", verbose=False, cache=None, silent=False):
    import zipfile
    report('\n[*] ' + str(url), silent)
    report('Starting download...', silent)
    try:
        to_file = '/download'
        if url.endswith(to_file):
            to_file = ''
        # Retrieving modpack
        dl_mp = urllib.request.urlopen(req(url + to_file, user_agent))
        resp = dl_mp.read()
        # Get the name for the file by getting the redirect from '/download' to 'something/something.extenshion'
        dl_mp = dl_mp.geturl()
        dl_mp = dl_mp.replace("%20", " ")
        filename = posixpath.basename(dl_mp)
        report('Downloading ' + filename, silent)
    except urllib.error.HTTPError as e:
        log_failed(str(e.code) + ' - ' + url, log, silent)
        return
    try:
        with open(filename, "wb") as f:
            f.write(resp)
    except (OSError, IOError) as e:
        log_failed(e, log, silent)
        log_failed('Unable to write data from ' + str(url) + ' to ' + str(filename), log, silent)
        return
    # Create new dir for extracted files
    dirname = filename
    # Why wouldn't it but hey...
    if filename.endswith('.zip'):
        dirname = dirname[:-4]
    # If Dir already exist
    if os.path.isdir(str(Path(dirname))):
        log_failed('Dir ' + str(dirname) + ' already exists.', log, silent)
        log_failed('To not go at risk of destroying data, the procedure will be stopped.', log, silent)
        return
    # Create the Dir
    os.makedirs(str(Path(dirname)))
    # Unzip the retrieved file
    zip_ref = zipfile.ZipFile(filename, 'r')
    zip_ref.extractall(str(Path(dirname)))
    zip_ref.close()
    # Delete the retrieved file
    os.remove(filename)
    # And now go and download the files
    dl(Path(dirname, 'manifest.json'), log=log, user_agent=user_agent, verbose=verbose, cache=cache, silent=silent)


def main():
    import argparse
    import re
    parser = argparse.ArgumentParser(description="dlcmp - download utility for curse mod packs")
    parser.add_argument("dest", metavar='destination', nargs='?', help="url or path (e.g. 'https://minecraft.curseforge.com/projects/invasion/files/2447205' or 'path/2/manifest.json')", default=None)
    parser.add_argument("--url", "--prefer-url", dest='prefer_url', help="positional argument will be handled as an URL", action='store_true', default=False)
    parser.add_argument("--path", "--prefer-path", dest='prefer_path', help="positional argument will be handled as a path", action='store_true', default=False)
    parser.add_argument("--ua", "--user-agent", metavar='user-agent-string', dest='useragent', help="User-Agent String", default='Mozilla/5.0 (Windows NT 6.1; WOW64; rv:37.0) Gecko/20100101 Firefox/37.0')  # http://techblog.willshouse.com/2012/01/03/most-common-user-agents/
    parser.add_argument("-v", "--verbose", dest='verbose', help="show verbose information", action='store_true', default=False)
    parser.add_argument("-l", "--log", dest='log', metavar='logfile', help="log failed requests (and some other stuff)", default=None)
    parser.add_argument("-c", "--cache", dest='cache', metavar='cachedir', help='path to cache directory')
    parser.add_argument("--silent", dest='silent', help="no output to cli", action='store_true', default=False)
    args, unknown = parser.parse_known_args()
    if args.verbose:
        report('Log: ' + str(args.log), args.silent)
        report('User-Agent: ' + str(args.useragent), args.silent)
    if args.dest is None:
        if not args.silent:
            parser.print_usage()
        report('No positional argument found. Aborting.', args.silent)
        return
    # Test, if it is a url (with bad regex) and not specified as path (or if it is specified as url)
    match = re.match(r'^(?:(?:http|ftp)s?://).*$', args.dest, re.IGNORECASE)
    if match and not args.prefer_path or args.prefer_url:
        get_modpack(args.dest, log=args.log, user_agent=args.useragent, verbose=args.verbose, cache=args.cache, silent=args.silent)
    # Specified as path?
    else:
        if not os.path.isfile(args.dest):
            report('No manifest found at %s' % args.dest, args.silent)
            return
        dl(args.dest, log=args.log, user_agent=args.useragent, verbose=args.verbose, cache=args.cache, silent=args.silent)


if __name__ == '__main__':
    main()
