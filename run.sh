#!/bin/sh
# Copyright (C) 2026 Roger Barthares
# SPDX-License-Identifier: GPL-3.0-only
# Nebula launcher: uses the PySide6 and libraries bundled next to this script.
SRC=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
CACHE_ROOT=${NEBULA_CACHE:-$HOME/.cache/Nebula}
DATA_ROOT=${NEBULA_DATA:-$HOME/Nebula}
mkdir -p "$CACHE_ROOT/tmp" "$DATA_ROOT"

# The native GTK file chooser reads GTK_THEME, not Qt's palette. Some desktops
# (Zorin) ship a light theme in /etc/gtk-3.0/settings.ini even while the live
# GNOME setting is dark. Read the desktop setting here, before the app starts;
# leave an explicit GTK_THEME alone.
if [ -z "${GTK_THEME:-}" ] && command -v gsettings >/dev/null 2>&1; then
    GTK_THEME_NAME=$(gsettings get org.gnome.desktop.interface gtk-theme 2>/dev/null | tr -d "'")
    GTK_COLOR_SCHEME=$(gsettings get org.gnome.desktop.interface color-scheme 2>/dev/null | tr -d "'")
    if [ -n "$GTK_THEME_NAME" ]; then
        case "$GTK_THEME_NAME" in
            Adwaita)
                [ "$GTK_COLOR_SCHEME" = "prefer-dark" ] && GTK_THEME_NAME="Adwaita:dark"
                ;;
        esac
        GTK_THEME=$GTK_THEME_NAME
        export GTK_THEME
    fi
fi


# Keep caches and scratch files made by Qt, fontconfig, Mesa and child tools in
# the Nebula cache. XDG_CONFIG_HOME and XDG_DATA_HOME are deliberately left at
# the desktop's own values: the native GTK chooser reads the system's user
# folders, bookmarks, recent files and GTK settings from them.
XDG_CACHE_HOME=$CACHE_ROOT
TMPDIR=$CACHE_ROOT/tmp
MESA_SHADER_CACHE_DIR=$CACHE_ROOT/mesa
PYTHONDONTWRITEBYTECODE=1
export XDG_CACHE_HOME TMPDIR MESA_SHADER_CACHE_DIR

DIR=$SRC

# An installed package (marked by BUNDLE_VERSION) runs from a copy in the cache
# folder, so the program, Qt and the libraries all sit in ~/.cache/Nebula. The
# copy is refreshed only when the package version changes.
if [ -f "$SRC/BUNDLE_VERSION" ]; then
    DIR=$CACHE_ROOT/app
    # no copy in /opt to refresh from: keep the cache copy and run it as it is
    if [ "$SRC" != "$DIR" ] && { [ ! -f "$DIR/BUNDLE_VERSION" ] || ! cmp -s "$SRC/BUNDLE_VERSION" "$DIR/BUNDLE_VERSION"; }; then
        TMP=$CACHE_ROOT/app.tmp.$$
        rm -rf "$TMP" "$DIR"
        mkdir -p "$TMP" && cp -a "$SRC/." "$TMP/" && mv "$TMP" "$DIR" || {
            rm -rf "$TMP"
            echo "Could not copy the app into $CACHE_ROOT." >&2
            exit 1
        }
    fi
fi
ASSETS="$DIR/assets"

if [ ! -d "$ASSETS/PySide6" ]; then
    echo "The assets folder is missing. Unzip the whole archive, keeping run.sh and assets together." >&2
    exit 1
fi

PYTHON=${PYTHON:-python3}
if ! command -v "$PYTHON" >/dev/null 2>&1; then
    echo "python3 was not found. Install Python 3.9 or newer (e.g. sudo apt install python3)." >&2
    exit 1
fi

# bundled libraries first: Qt's own libs, codecs, and the X11 bits minimal
# installs tend to miss. System libs (glibc, libstdc++, X11) still come from the OS.
LD_LIBRARY_PATH="$ASSETS/lib:$ASSETS/lib/pulseaudio:$ASSETS/PySide6/Qt/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export LD_LIBRARY_PATH
QT_PLUGIN_PATH="$ASSETS/PySide6/Qt/plugins"
export QT_PLUGIN_PATH

# only override fontconfig when the system has no font configuration at all
if [ ! -f /etc/fonts/fonts.conf ]; then
    FONTCONFIG_FILE="$ASSETS/fonts.conf"
    export FONTCONFIG_FILE
fi

if [ "$1" = "--check" ]; then
    exec "$PYTHON" - "$DIR" <<'PY'
import os, sys
root = sys.argv[1]
sys.path.insert(0, os.path.join(root, "assets"))
import mutagen, PySide6
from PySide6 import QtCore
print("python  :", sys.version.split()[0])
print("PySide6 :", PySide6.__version__, "from", os.path.dirname(PySide6.__file__))
print("Qt      :", QtCore.qVersion())
print("mutagen :", ".".join(map(str, mutagen.version)))
print("assets  :", "ok" if os.path.isdir(os.path.join(root, "assets", "PySide6", "Qt", "plugins")) else "missing")
PY
fi

exec "$PYTHON" "$DIR/nebula.py" "$@"
