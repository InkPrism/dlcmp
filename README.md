***

<h1 align="center">
	<b>dlcmp</b>
</h1>
<h3 align="center">
	<i>download utility for curse mod packs</i>
</h3>

### Features
* Download mod pack archive and download the mods from the manifest.json  
```
$  dlcmp.py https://minecraft.curseforge.com/projects/invasion/files/2447205
```
* Download mods from already unzipped manifest  
```
$  dlcmp.py path/2/manifest.json
```
* Normally, dlcmp will be able to distinguish between the two, yet if there are issues, one can use:
	* ```--url```, ```--prefer-url```
	* ```--path```, ```--prefer-path```
* A cache directory can be specified. (Compatible with the ones created by [portablejim's curseDownloader](https://github.com/portablejim/curseDownloader))
```
$ dlcmp.py -c path/2/cache/ ...
```
* If a mod site is unavailable, it will be skipped
* If the file already exists, it will not be downloaded again  
* No dependencies other than the [Python Standard Library](https://docs.python.org/library/ "Python Standard Library")

### Have fun