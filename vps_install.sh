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

    if [ "$USER" != "root" ] ; then
	err "you need to run as root"
    fi

    if [ -x /usr/bin/apt-cache ] ; then
	info "Debian/Ubuntu type system detected"
	install_deb
    else
	if [ -x /usr/bin/yum ] ; then
	    info "RedHat/CentOS/Fedora type system detected"
	    install_yum
	else
	    if [ -x /usr/bin/pacman ] ; then
		info "Arch system detected"
		install_arch
	    else
		err "cannot detect system type: no apt-get, yum or pacman"
	    fi
	fi
    fi	    

    need_cmd pip3
    ensure pip3 install https://github.com/ihaywood3/DEXBot/archive/master.zip

    need_cmd useradd
    need_cmd passwd
    need_cmd loginctl
    useradd dexbot -s /usr/local/bin/dexbot-shell
    echo
    info "Please enter a new password for the \"dexbot\" account on this computer."
    ensure passwd dexbot < /dev/tty
    ensure loginctl enable-linger dexbot

    success "Configuration complete, now logout, and log in again as user dexbot"
    success "using the password you provided above. The dexbot configuration"
    success "will continue at that point."
}

install_deb() {
    need_cmd apt-get
    ensure apt-get update
    apt-cache show python3-pip > /dev/null 2> /dev/null
    if [ "$?" != 0 ] ; then
	warn "Some packages aren't available"
	warn "trying to enable the Ubuntu 'universe' repository"
	ensure apt-get install -y software-properties-common
	ensure add-apt-repository universe
	ensure apt-get update
	apt-cache show python3-pip > /dev/null 2>&1
	if [ "$?" != 0 ] ; then
	    err "universe repository still not available"
	fi
    fi
    
    ensure apt-get install -y gcc libssl-dev python3-pip python3-dev build-essential python3-setuptools python3-wheel whiptail passwd systemd
}

install_yum() {
    ensure yum install -y gcc openssl-devel python3-pip python3-devel newt
}

install_arch() {
    ensure pacman -S libnewt python-pip gcc
}

info() {       	
    if $_ansi_escapes_are_valid; then
        printf "\33[1minfo:\33[0m %s\n" "$1" 1>&2
    else
        printf 'info: %s\n' "$1" 1>&2
    fi
}

err() {
    if $_ansi_escapes_are_valid; then
        printf "\33[1m\33[31mERROR:\33[0m %s\n" "$1" 1>&2
    else
        printf 'ERROR: %s\n' "$1" 1>&2
    fi    	

    exit 1
}

warn() {
    if $_ansi_escapes_are_valid; then
        printf "\33[1m\33[36mWARNING: \33[0m %s\n" "$1" 1>&2
    else
        printf 'WARNING: %s\n' "$1" 1>&2
    fi
}

success() {
    if $_ansi_escapes_are_valid; then
        printf "\33[1m\33[32mSUCCESS: \33[0m %s\n" "$1" 1>&2
    else
        printf 'SUCCESS: %s\n' "$1" 1>&2
    fi
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
