#!/bin/sh
if [ $# -eq 0 ]; then
    FLAVOR=gtk
    if ! python -c 'import gtk' && python -c 'import tkinter'; then
        FLAVOR=tk
    fi
else
    FLAVOR=$1
fi

case $FLAVOR in
gtk)
    echo "Installing gtk version of cropgui"
    cp cropgtk.py $HOME/bin/cropgui && \
    cp cropgui_common.py filechooser.py cropgui.glade $HOME/lib/python
;;
tk)
    echo "Installing tkinter version of cropgui"
    cp cropgui.py $HOME/bin/cropgui && \
    cp cropgui_common.py $HOME/lib/python
;;
*)
    echo "Unknown flavor $FLAVOR"
    exit 1
;;
esac

if [ $? -ne 0 ]; then exit $?; fi

chmod +x $HOME/bin/cropgui

if ! python -c 'import cropgui_common' 2>&1; then
    echo "*** Failed to import cropgui_common.py: add $HOME/lib/python to PYTHONPATH"
    exit 1
fi

echo "Installed cropgui $FLAVOR"

#    installation script for cropgui, a graphical front-end for lossless jpeg
#    cropping
#    Copyright (C) 2009 Jeff Epler <jepler@unpythonic.net>
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
