# WeeChat scripts by FiXato
******************************************************************************

My personal repository of scripts for the WeeChat chat client, www.weechat.org

Scripts I've written to add features to WeeChat I felt were missing.

## Overview

* clone_scanner.py
    Detect if a joining user is a clone or not.
* listbuffer.py (for now still in its own repository, but will be added later)
    Show /list results in a common buffer and interact with them.


## Configuration instructions
******************************************************************************


## History
******************************************************************************

See headers of individual scripts for their Changelogs.


## Notes on Patches/Pull Requests
******************************************************************************

1. Fork the project.
2. Make your feature addition or bug fix.
3. Add tests for it (even though I don't have tests myself at the moment). 
  This is important so I don't break it in a future version unintentionally.
4. Commit, but do not mess with gemspec, version, history, or README.
  Want to have your own version? Bump version in a separate commit!
  That way I can ignore that commit when I pull.
5. Send me a pull request. Bonus points for topic branches.
6. You'll be added to the credits.

## Acknowledgements
******************************************************************************

Thanks go out to:

* Sebastien "Flashcode" Helleu, for developing the kick-ass IRC client WeeChat
    and the iset.pl script which inspired me to write listbuffer.py.
* Nils "nils_2" Görs, for his contributions to iset.pl which served as
    example code for listbuffer.py.
* David "drubin" Rubin, for his urlgrab.py script, which also served
    as example code for listbuffer.py.
* ArZa, whose listsort.pl script helped me getting started with 
    grabbing the /list results for listbuffer.py and whose kickban.pl script
    served as an example for handling infolists for clone_scanner.py.
* Khaled Mardam-Bey, for making me yearn for similar /list support in 
    WeeChat as mIRC already offered. :P


## Copyright
******************************************************************************

Copyright (c) 2011 Filip H.F. "FiXato" Slagter,
    <FiXato [at] Gmail [dot] com>
    http://google.com/profiles/FiXato

See LICENSE for details.