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

def create_parser():
    parser = argparse.ArgumentParser(description='UERANSIM Satellite CLI Tool')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Start command
    start_parser = subparsers.add_parser('start', help='Start connection to a core network')
    start_parser.add_argument('corenet', choices=['open5gs1', 'open5gs2'], 
                             help='Core network to connect to')
    start_parser.add_argument('--output', '-o', default=None, 
                             help='Output file for logs')
    start_parser.add_argument('--gen-time', '-t', type=float, default=30.0,
                             help='Traffic generation time in seconds')
    
    # Switch command
    switch_parser = subparsers.add_parser('switch', help='Switch to a different core network')
    switch_parser.add_argument('corenet', choices=['open5gs1', 'open5gs2'], 
                              help='Core network to switch to')
    switch_parser.add_argument('--output', '-o', default=None, 
                              help='Output file for logs')
    switch_parser.add_argument('--gen-time', '-t', type=float, default=30.0,
                              help='Traffic generation time in seconds')
    
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
        start_command(args.corenet, args.output, args.gen_time)
    elif args.command == 'switch':
        switch_command(args.corenet, args.output, args.gen_time)
    elif args.command == 'stop':
        stop_command()

if __name__ == "__main__":
    main()


