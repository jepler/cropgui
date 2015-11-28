#!/bin/sh
PYTHON=python2
BINDIR=$HOME/bin; LIBDIR=$HOME/lib/python SHAREDIR=$HOME/share

default_flavor () {
    if ! $PYTHON -c 'import gtk' >/dev/null 2>&1 \
                && $PYTHON -c 'import tkinter' > /dev/null 2>&1; then
        echo tk
    else
        echo gtk
    fi
}

site_packages () {
    $PYTHON -c 'import distutils.sysconfig; print distutils.sysconfig.get_python_lib()'
}

usage () {
    cat <<EOF
Usage: ./install.sh [-f tk|gtk] [-u|-p PREFIX] [-P PYTHON] [-t TARGET]
    -f: choose the flavor to install
    -u: install to $HOME
    -p: install to $PREFIX
    -P: Python executable to use
    -t: install inside TARGET (for package building)
EOF
    exit
}

while getopts "f:ut:p:P:" opt
do
    case "$opt" in
    f) FLAVOR=$OPTARG ;;
    u) BINDIR=$HOME/bin; LIBDIR=$HOME/lib/python; SHAREDIR=$HOME/share ;;
    t) TARGET=$OPTARG ;;
    P) PYTHON=$OPTARG ;;
    p) FPYTHON=`which $PYTHON`;
       BINDIR=`dirname $FPYTHON`;
       SHAREDIR=`dirname $BINDIR`/share;
       LIBDIR=`site_packages $PYTHON` ;;
    *) usage ;;
    esac
done

if [ -z "$FLAVOR" ]; then FLAVOR=`default_flavor`; fi

mkdir -p $TARGET$BINDIR $TARGET$LIBDIR $TARGET$SHAREDIR/applications \
    $TARGET$SHAREDIR/pixmaps

cp cropgui.desktop $TARGET$SHAREDIR/applications
cp cropgui.png $TARGET$SHAREDIR/pixmaps

case $FLAVOR in
gtk)
    echo "Installing gtk version of cropgui"
    cp cropgtk.py $TARGET$BINDIR/cropgui && \
    cp cropgui_common.py filechooser.py cropgui.glade \
        stock-rotate-90-16.png stock-rotate-270-16.png \
        $TARGET$LIBDIR
;;
tk)
    echo "Installing tkinter version of cropgui"
    cp cropgui.py $TARGET$BINDIR/cropgui && \
    cp log.py cropgui_common.py $TARGET$LIBDIR
;;
*)
    echo "Unknown flavor $FLAVOR"
    exit 1
;;
esac

if [ $? -ne 0 ]; then exit $?; fi

chmod +x $TARGET$BINDIR/cropgui

if [ -z "$TARGET" ] && ! (cd /tmp; $PYTHON -c 'import cropgui_common') > /dev/null 2>&1; then
    echo "*** Failed to import cropgui_common.py"
    echo "    You must add $LIBDIR to PYTHONPATH"
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
