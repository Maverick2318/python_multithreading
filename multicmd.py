#!/usr/bin/env python3

from argparse import ArgumentParser
from fabric import Connection
from os import path
from threading import Thread

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
            result = conn.run(cmd,
                              echo=True,
                              encoding='utf-8',
                              hide=True,
                              timeout=timeout,
                            )
            out = result.stdout
    output[host] = out


def parse_args():
    '''
    Parse args for the script.
    '''
    parser = ArgumentParser()

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

    parser.add_argument('-c', '--cmd',
                        help='Command to run on remote hosts',
                        nargs='+',
                        required=True,
                        )

    parser.add_argument('-t', '--timeout',
                        action='store',
                        default=15,
                        help='Timeout for the command to run',
                        type=int,
                        )

    args = parser.parse_args()

    if not args.hostlist and not args.filename:
        args.print_help()
        sys.exit(0)

    return args

def run_threads(h_list: list, cmd: str, timeout: int) -> dict:
    '''
    Run command on the hosts and return outputs
    '''
    output = {}
    threads = []
    for host in h_list:
        t = Thread(target=runner, args=(cmd, host, timeout, output,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    return output


def run(args):
    host_list = []

    if args.hostlist:
        host_list = args.hostlist

    if args.filename:
        file_hosts = load_hosts_from_file(args.filename)
        host_list.extend(file_hosts)
        
    output_dict = run_threads(host_list, ' '.join(args.cmd), args.timeout)
    formatted_output(output_dict)

    return

if __name__ == '__main__':
    args = parse_args()
    run(args)
