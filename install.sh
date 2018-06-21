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
    need_cmd uname
    need_cmd curl

    
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
	err "you need to run via sudo"
    fi
    if [ -z "$SUDO_USER" ] ; then
	err "you need to run via sudo"
    fi
    if [ "$SUDO_USER" == "root" ] ; then
	err "you need to run as an ordinary user"
    fi

    need_cmd loginctl
    ensure loginctl enable-linger $SUDO_USER

    if [ ! -x /usr/bin/apt-cache ] ; then
	err "apt-cache not found: are you running Ubuntu/Debian?"
    fi
    need_cmd apt-get
    
    apt-cache show libssl-dev > /dev/null 2> /dev/null
    if [ "$?" != 0 ] ; then
	echo "Some packages aren't available"
	echo "trying to enable the Ubuntu 'universe repository"
	ensure apt-get update
	ensure apt-get install -y software-properties-common
	ensure add-apt-repository universe
	ensure apt-get update
	apt-cache show libssl-dev > /dev/null 2> /dev/null
	if [ "$?" != 0 ] ; then
	    err "universe repository still not available"
	fi
    fi
    
    ensure apt-get install -y gcc libssl-dev python3-pip python3-dev build-essential python3-setuptools python3-wheel whiptail

    ensure sudo -H pip3 install https://github.com/Codaone/DEXBot/archive/master.zip
    echo
    echo Next the 'uptick' program is being used to import private keys
    echo uptick will ask you first for a passphrase to protect private keys stored in
    echo its wallet. This has no relation to any passphrase used in the web wallet.
    echo You can get your private key from the BitShares Web Wallet: click the menu
    echo on the top right, then \"Settings\", \"Accounts\", \"View keys\", then tab
    echo \"Owner Permissions\", click on the public key, then \"Show\".
    echo Look for the private key in Wallet Import Format \(WIF\), it’s a \"5\" followed
    echo by a long list of letters. Select, copy and paste this into the screen where
    echo uptick asks for the key.
    ensure su $SUDO_USER -c "uptick addkey"
    ensure su $SUDO_USER -c "dexbot-cli configure"
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
