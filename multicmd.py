#!/usr/bin/env python3

from argparse import ArgumentParser
from fabric import Connection
from invoke.exceptions import CommandTimedOut, UnexpectedExit
from os import path
import sys
from threading import Thread
from time import sleep

def formatted_output(output: dict):
    '''
    Print output in a formatted fashion
    '''
    out = ''
    buff = '*'*15
    for key in sorted(output):
        out += f'{buff} {key} {buff}\n{output.get(key)}\n'

    print(out)


def load_hosts_from_file(filename: str):
    '''
    Attempt to load hosts from a file.
    '''
    if not path.exists(filename):
        err = f'Path {filename} does not exist'
        print(err)
        return []

    with open(filename, 'r') as f:
        lines = f.readlines()

    return [l.strip() for l in lines if l.strip()]

def runner(cmd: str, host: str, timeout: int, output: dict):
    '''
    Runs a the given command on the remote host.
    '''
    kwargs = {'forward_agent': True}
    with Connection(host, **kwargs) as conn:
        conn.open()
        if not conn.is_connected:
            out = 'Unable to connect to host'
        else:
            try:
                result = conn.run(cmd,
                                  echo=True,
                                  encoding='utf-8',
                                  hide=True,
                                  timeout=timeout,
                                )
                out = result.stdout
            except CommandTimedOut as e:
                out = 'ERROR: Command Timeout (did not complete within '\
                     f'{timeout} seconds)'
            except UnexpectedExit as e:
                out = e

    output[host] = out

def parse_args():
    '''
    Parse args for the script.
    '''
    parser = ArgumentParser()

    parser.add_argument('-c', '--cmd',
                        help='Command to run on remote hosts',
                        nargs='+',
                        required=True,
                        )

    parser.add_argument('-d', '--display',
                        action='store_true',
                        default=False,
                        help='Display hosts command is still running on',
                        )

    parser.add_argument('-f', '--filename',
                        action='store',
                        default='',
                        help='File to read hostnames from',
                        type=str,
                        )

    parser.add_argument('-l', '--hostlist',
                        default=[],
                        help='List of hosts to run commands on',
                        nargs='+',
                        )

    parser.add_argument('-t', '--timeout',
                        action='store',
                        default=15,
                        help='Timeout for the command to run',
                        type=int,
                        )

    args = parser.parse_args()

    if not args.hostlist and not args.filename:
        parser.print_help(sys.stderr)
        sys.exit(0)

    return args

def run_threads(h_list: list,
                cmd: str,
                timeout: int,
                display_unfinished: bool = True,
                ) -> dict:
    '''
    Run command on the hosts and return outputs
    '''
    def display_active(interval=5):
        '''
        Prints the hosts in which the command is waiting to finish on
        every 5 seconds.
        '''
        cur = 1
        sleeptime = .5
        converted_interval = interval/sleeptime
        while True:
            active = [thread_dict.get(t) for t in thread_dict if t.is_alive()]
            
            if not active:
                break

            if cur >= converted_interval:
                hosts = '\n'.join(active)
                msg = '-------------------------\n'\
                     f'Waiting on: \n{hosts}'
                print(msg)
                cur = 1
            else:
                cur += 1

            sleep(sleeptime)
        return

    output = {}
    thread_dict = {}

    for host in h_list:
        t = Thread(target=runner, args=(cmd, host, timeout, output,))
        t.start()
        thread_dict[t] = f'  {host}'

    if display_unfinished:
        display_thread = Thread(target=display_active,)
        display_thread.start()
        
    for t in thread_dict:
        t.join()

    return output


def run(args):
    host_list = []

    if args.hostlist:
        host_list = args.hostlist

    if args.filename:
        file_hosts = load_hosts_from_file(args.filename)
        host_list.extend(file_hosts)
        
    output_dict = run_threads(host_list,
                              ' '.join(args.cmd),
                              args.timeout,
                              display_unfinished=args.display)
    formatted_output(output_dict)

    return

if __name__ == '__main__':
    args = parse_args()
    run(args)
