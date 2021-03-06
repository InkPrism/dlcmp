***

<h1 align="center">
	<b>dlcmp</b>
</h1>
<h3 align="center">
	<i>download utility for curse mod packs</i>
</h3>

### Features
* Download mod pack archive and download the mods from the manifest.json  
	* ```$  dlcmp.py https://minecraft.curseforge.com/projects/invasion/files/2447205```
	* Use ```-o path/2/outputdir/``` to specify the output directory
* Download mods from already unzipped manifest  
	* ```$  dlcmp.py path/2/manifest.json```
* Normally, dlcmp will be able to distinguish between the two, yet if there are issues, one can use:
	* ```--url```, ```--prefer-url```
	* ```--path```, ```--prefer-path```
* A cache directory can be specified. (Compatible with the ones created by [portablejim's curseDownloader](https://github.com/portablejim/curseDownloader))
	* ```$ dlcmp.py -c path/2/cache/ ...```
* If a mod site is unavailable, it will be skipped
* All failed requests will be noted in a logfile
	* ```$ dlcmp.py -l path/2/logfile ...```
* Use ```--silent``` to silence output to the command line
* ```--ua useragentstring``` specifies an user agent string
* ```-v``` shows verbose information
* If the file already exists, it will not be downloaded again  
* No dependencies other than the [Python Standard Library](https://docs.python.org/library/ "Python Standard Library")
* single file

### Have fun