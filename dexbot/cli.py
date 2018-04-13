#!/usr/bin/env python3
import logging
import os
# we need to do this before importing click
if not "LANG" in os.environ:
    os.environ['LANG'] = 'C.UTF-8'
import click
import signal
import os.path
import os
import sys
import appdirs

from .ui import (
    verbose,
    chain,
    unlock,
    configfile
)

from dexbot.worker import WorkerInfrastructure
from .cli_conf import configure_dexbot
import dexbot.errors as errors

import click

log = logging.getLogger(__name__)

# inital logging before proper setup.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)


@click.group()
@click.option(
    "--configfile",
    default=os.path.join(appdirs.user_config_dir("dexbot"), "config.yml"),
)
@click.option(
    '--verbose',
    '-v',
    type=int,
    default=3,
    help='Verbosity (0-15)')
@click.option(
    '--systemd/--no-systemd',
    '-d',
    default=False,
    help='Run as a daemon from systemd')
@click.option(
    '--pidfile',
    '-p',
    type=str,
    default='',
    help='File to write PID')
@click.pass_context
def main(ctx, **kwargs):
    ctx.obj = {}
    for k, v in kwargs.items():
        ctx.obj[k] = v


@main.command()
@click.pass_context
@configfile
@chain
@unlock
@verbose
def run(ctx):
    """ Continuously run the worker
    """
    if ctx.obj['pidfile']:
        with open(ctx.obj['pidfile'], 'w') as fd:
            fd.write(str(os.getpid()))
    try:
        try:
            worker = WorkerInfrastructure(ctx.config)
            # Set up signalling. we do it here as it's of no relevance to GUI
            kill_workers = worker_job(worker, worker.stop)
            # These first two signals UNIX & Windows
            signal.signal(signal.SIGTERM, kill_workers)
            signal.signal(signal.SIGINT, kill_workers)
            try:
                # These signals are UNIX-only territory, will throw exception at this point on Windows
                signal.signal(signal.SIGHUP, kill_workers)
                # TODO: reload config on SIGUSR1
                # signal.signal(signal.SIGUSR1, lambda x, y: worker.do_next_tick(worker.reread_config))
            except AttributeError:
                log.debug("Cannot set all signals -- not available on this platform")
            worker.run()
        finally:
            if ctx.obj['pidfile']:
                os.unlink(ctx.obj['pidfile'])
    except errors.NoWorkersAvailable:
        sys.exit(70)  # 70= "Software error" in /usr/include/sysexts.h

@main.command()
@click.pass_context
def configure(ctx):
    """ Interactively configure dexbot
    """
    cfg_file = ctx.obj["configfile"]
    if os.path.exists(ctx.obj['configfile']):
        with open(ctx.obj["configfile"]) as fd:
            config = yaml.load(fd)
    else:
        config = {}
        storage.mkdir_p(os.path.dirname(ctx.obj['configfile']))
    configure_dexbot(config)
    with open(cfg_file, "w") as fd:
        yaml.dump(config, fd, default_flow_style=False)
    click.echo("new configuration saved")
    if config['systemd_status'] == 'installed':
        # we are already installed
        click.echo("restarting dexbot daemon")
        os.system("systemctl --user restart dexbot")
    if config['systemd_status'] == 'install':
        os.system("systemctl --user enable dexbot")
        click.echo("starting dexbot daemon")
        os.system("systemctl --user start dexbot")

def worker_job(worker, job):
    return lambda x, y: worker.do_next_tick(job)

if __name__ == '__main__':
    main()
