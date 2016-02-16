periscope (branch: subsearch)
============
Fork of periscope used for downloading subtitles for given video file(s) from SubHeaven.org or SubFinland.org through Subsearch.org's search engine

* [Project page for original periscope](http://code.google.com/p/periscope/)

Differences to standard periscope
============
 - No support for other plugins except SubSearch (new standards that I didn't add to other providers)
 - Lesser available parameters
 - More automation. Functionality to provide wider searching and better filenaming.
 - Adds .fi before .srt/.sub as a language code

Usage
============
Execute periscope.py from folder where you want your subtitle file to be downloaded with argument either to path containing a video file(s) or video's filename.

Examples
============
Usage examples:
```
#cd /subtitles
#/path/to/periscope.py /videos/Arrow.S04E05.HDTV.x264-LOL.mp4
```
or 
```
#cd /subtitles
#/path/to/periscope.py /videos
```
Pass either a filename or path containing filename as argument to search and download subtitles to path where periscope was executed from.

Troubleshooting
============
If you do as explained in the examples, notice that file /videos/Arrow.S04E05.HDTV.x264-LOL.mp4 must exist, but it doesn't need to be the actual video file, it is enough to use touch so that filename exists.
