#!/usr/bin/env python3
import sys
import os
import argparse
import logging
from cmds.start import start_command
from cmds.switch import switch_command
from cmds.stop import stop_command
from cmds.admin import check_admin
from cmds.help_msg import show_help


logging.basicConfig(level=logging.INFO)


class CustomArgumentParser(argparse.ArgumentParser):
    # -h / --help can be caught by default.
    # then it will be redirected to "help" function
    def print_help(self, file=None):
        show_help()
    
    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(2, f"{self.prog}: error: {message}\n")


def create_parser():
    parser = CustomArgumentParser(description='UERANSIM Satellite CLI Tool')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Start command
    start_parser = subparsers.add_parser('start', help='Start connection to a core network')
    start_parser.add_argument('corenet', choices=['open5gs1', 'open5gs2'], 
                             help='Core network to connect to')
    start_parser.add_argument('--output', '-o', default=None, 
                             help='Output file for logs')
        
    # Switch command
    switch_parser = subparsers.add_parser('switch', help='Switch to a different core network')
    switch_parser.add_argument('corenet', choices=['open5gs1', 'open5gs2'], 
                              help='Core network to switch to')
    switch_parser.add_argument('--output', '-o', default=None, 
                              help='Output file for logs')
    
    # Stop command
    stop_parser = subparsers.add_parser('stop', help='Stop current connection')
    
    # Help command
    help_parser = subparsers.add_parser('help', help='Show detailed help information')
    
    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()
    
    # If no command provided or help command, show help
    if not args.command or args.command == 'help':
        show_help()
        return
    
    # Check admin permissions for commands that need it
    if args.command in ['start', 'switch', 'stop'] and not check_admin():
        sys.exit(1)
    
    # Execute command
    if args.command == 'start':
        start_command(args.corenet, args.output)
    elif args.command == 'switch':
        switch_command(args.corenet, args.output)
    elif args.command == 'stop':
        stop_command()


if __name__ == "__main__":
    main()
    
    
