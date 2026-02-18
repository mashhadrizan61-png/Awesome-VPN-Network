#!/usr/bin/env python3
"""Virtual Modem Lab

A local/offline lab tool for organizing VPS and VPN profiles and generating
starter configuration templates.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

DB_PATH = Path("lab_profiles.json")


@dataclass
class VpsProfile:
    name: str
    host: str
    region: str
    ssh_port: int = 22


@dataclass
class VpnProfile:
    name: str
    protocol: str
    endpoint: str
    port: int


class ProfileStore:
    def __init__(self, path: Path = DB_PATH) -> None:
        self.path = path
        self.data = self._load()

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"vps": [], "vpn": []}
        with self.path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _save(self) -> None:
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump(self.data, handle, indent=2, ensure_ascii=False)

    def add_vps(self, profile: VpsProfile) -> None:
        self.data["vps"].append(asdict(profile))
        self._save()

    def add_vpn(self, profile: VpnProfile) -> None:
        self.data["vpn"].append(asdict(profile))
        self._save()

    def list_all(self) -> dict[str, Any]:
        return self.data


def generate_wireguard_template(client_private_key: str, server_public_key: str, server_endpoint: str, server_port: int) -> str:
    return f"""[Interface]
PrivateKey = {client_private_key}
Address = 10.13.13.2/24
DNS = 1.1.1.1

[Peer]
PublicKey = {server_public_key}
Endpoint = {server_endpoint}:{server_port}
AllowedIPs = 0.0.0.0/0, ::/0
PersistentKeepalive = 25
"""


def modem_report(store: ProfileStore) -> str:
    vps_count = len(store.data.get("vps", []))
    vpn_count = len(store.data.get("vpn", []))
    recommendation = "Need at least one VPS and one VPN profile" if not (vps_count and vpn_count) else "Lab is ready for deployment simulation"
    return (
        "Virtual Modem Status\n"
        "-------------------\n"
        f"Configured VPS profiles: {vps_count}\n"
        f"Configured VPN profiles: {vpn_count}\n"
        f"Recommendation: {recommendation}\n"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Local virtual modem lab helper. "
            "Use responsibly and comply with local laws and service terms."
        )
    )
    sub = parser.add_subparsers(dest="command", required=True)

    add_vps = sub.add_parser("add-vps", help="Add a VPS profile")
    add_vps.add_argument("--name", required=True)
    add_vps.add_argument("--host", required=True)
    add_vps.add_argument("--region", required=True)
    add_vps.add_argument("--ssh-port", type=int, default=22)

    add_vpn = sub.add_parser("add-vpn", help="Add a VPN profile")
    add_vpn.add_argument("--name", required=True)
    add_vpn.add_argument("--protocol", choices=["wireguard", "openvpn", "socks5"], required=True)
    add_vpn.add_argument("--endpoint", required=True)
    add_vpn.add_argument("--port", type=int, required=True)

    sub.add_parser("list", help="Show configured profiles")
    sub.add_parser("simulate-modem", help="Show virtual modem readiness report")

    wg = sub.add_parser("wg-template", help="Generate a WireGuard client template")
    wg.add_argument("--client-private-key", required=True)
    wg.add_argument("--server-public-key", required=True)
    wg.add_argument("--server-endpoint", required=True)
    wg.add_argument("--server-port", type=int, default=51820)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    store = ProfileStore()

    if args.command == "add-vps":
        store.add_vps(VpsProfile(name=args.name, host=args.host, region=args.region, ssh_port=args.ssh_port))
        print(f"Added VPS profile '{args.name}'.")
        return

    if args.command == "add-vpn":
        store.add_vpn(VpnProfile(name=args.name, protocol=args.protocol, endpoint=args.endpoint, port=args.port))
        print(f"Added VPN profile '{args.name}'.")
        return

    if args.command == "list":
        print(json.dumps(store.list_all(), indent=2, ensure_ascii=False))
        return

    if args.command == "simulate-modem":
        print(modem_report(store))
        return

    if args.command == "wg-template":
        print(
            generate_wireguard_template(
                client_private_key=args.client_private_key,
                server_public_key=args.server_public_key,
                server_endpoint=args.server_endpoint,
                server_port=args.server_port,
            )
        )
        return


if __name__ == "__main__":
    main()
