#!/bin/sh
# "borrowed" from the Rust installer
# adapted by Ian Haywood 2018

# Copyright 2016 The Rust Project Developers. See the COPYRIGHT
# file at the top-level directory of this distribution and at
# http://rust-lang.org/COPYRIGHT.
#
# Licensed under the Apache License, Version 2.0 <LICENSE-APACHE or
# http://www.apache.org/licenses/LICENSE-2.0> or the MIT license
# <LICENSE-MIT or http://opensource.org/licenses/MIT>, at your
# option. This file may not be copied, modified, or distributed
# except according to those terms.

set -u

main() {
    
    if [ -t 2 ]; then
        if [ "${TERM+set}" = 'set' ]; then
            case "$TERM" in
                xterm*|rxvt*|urxvt*|linux*|vt*)
                    _ansi_escapes_are_valid=true
                ;;
            esac
        fi
    fi

    	
    if $_ansi_escapes_are_valid; then
        printf "\33[1minfo:\33[0m checking system\n" 1>&2
    else
        printf '%s\n' 'info: checking system' 1>&2
    fi

    if [ "$USER" != "root" ] ; then
	err "you need to run as root"
    fi

    if [ ! -x /usr/bin/apt-cache ] ; then
	err "apt-cache not found: are you running Ubuntu/Debian?"
    fi
    need_cmd apt-get
    ensure apt-get update
    apt-cache show python3-pip > /dev/null 2> /dev/null
    if [ "$?" != 0 ] ; then
	echo "Some packages aren't available"
	echo "trying to enable the Ubuntu 'universe' repository"
	ensure apt-get install -y software-properties-common
	ensure add-apt-repository universe
	ensure apt-get update
	apt-cache show python3-pip > /dev/null 2>&1
	if [ "$?" != 0 ] ; then
	    err "universe repository still not available"
	fi
    fi
    
    ensure apt-get install -y gcc libssl-dev python3-pip python3-dev build-essential python3-setuptools python3-wheel whiptail passwd systemd

    need_cmd pip3
    ensure pip3 install https://github.com/ihaywood3/DEXBot/archive/master.zip

    need_cmd useradd
    need_cmd passwd
    need_cmd loginctl
    useradd dexbot -s /usr/local/bin/dexbot-shell
    echo
    echo Please enter a new password for the \"dexbot\" account on this computer.
    passwd dexbot
    ensure loginctl enable-linger dexbot

    echo Configuration complete, now logout, and log in again as user dexbot
    echo using the password you provided above. The dexbot configuration
    echo will continue at that point.
}

say() {
    echo "dexbot: $1"
}

err() {
    say "ERROR: $1" >&2
    exit 1
}

need_cmd() {
    if ! command -v "$1" > /dev/null 2>&1
    then err "need '$1' (command not found)."
    fi
}

need_ok() {
    if [ $? != 0 ]; then err "$1"; fi
}

assert_nz() {
    if [ -z "$1" ]; then err "assert_nz $2"; fi
}

# Run a command that should never fail. If the command fails execution
# will immediately terminate with an error showing the failing
# command.
ensure() {
    "$@"
    need_ok "command failed: $*"
}

# This is just for indicating that commands' results are being
# intentionally ignored. Usually, because it's being executed
# as part of error handling.
ignore() {
    "$@"
}

main "$@" || exit 1
