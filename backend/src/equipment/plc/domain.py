# Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
# SPDX-License-Identifier: Apache-2.0

import dataclasses
import inspect

from src import abstract, equipment


@dataclasses.dataclass
class Address(abstract.Domain):
    """Base class for address settings
    Attributes:
        enable (bool): Enabled
        name (str): Name
        address (str): Address
    """
    enable: bool = True
    name:str =""
    address: str = ""

    @classmethod
    def make_form(cls):
        """Create the settings form
        Returns:
            dict: Settings form
        """
        return {
            "enable": {
                "type": "switch",
                "label": "有効",
            },
            "name": {
                "type": "text",
                "label": "名前",
            },
            "address": {
                "type": "text",
                "label": "アドレス",
            }
        }


@dataclasses.dataclass
class BitAddress(Address):
    """Bit address settings
    Attributes:
        enable (bool): Enabled
        name (str): Name
        address (str): Address
        bit (int): Bit
        default (bool|None): Initial value
        data (bool): Data
    """
    bit: int = 0
    default: bool|None = None

    def __post_init__(self):
        """Post-initialization processing"""
        self.data = self.default if self.default is not None else False

    @classmethod
    def make_form(cls):
        """Create the settings form
        Returns:
            dict: Settings form
        """
        return super().make_form() | {
            "bit": {
                "type": "number",
                "label": "ビット",
                "integer": True,
                "min": 0,
                "max": 15,
            },
            "default": {
                "type": "select",
                "label": "既定値",
                "items": {"読取り専用": None, "1": True, "0": False},
                "required": False,
            }
        }


@dataclasses.dataclass
class WordAddress(Address):
    """Word address settings
    Attributes:
        enable (bool): Enabled
        name (str): Name
        address (str): Address
        data (int): Data
    """
    def __post_init__(self):
        """Post-initialization processing"""
        self.data = 0


@dataclasses.dataclass
class CycleBitAddress(Address):
    """Cyclic bit address settings
    Attributes:
        enable (bool): Enabled
        name (str): Name
        address (str): Address
        bit (int): Bit
        interval (float): Update cycle in seconds
    """
    bit: int = 0
    interval: float = 1.0

    def __post_init__(self):
        """Post-initialization processing"""
        self.data = False

    @classmethod
    def make_form(cls):
        """Create the settings form
        Returns:
            dict: Settings form
        """
        return super().make_form() | {
            "bit": {
                "type": "number",
                "label": "ビット",
                "integer": True,
                "min": 0,
                "max": 15,
            },
            "interval": {
                "type": "number",
                "label": "更新周期",
                "suffix": "秒",
            },
        }


@dataclasses.dataclass
class NodeDomain(abstract.Domain):
    """PLC node domain
    Attributes:
        enable (bool): Enabled
        name (str): Name
        location (list[float]): Location
        interface (str): Interface
        ip (str): IP address
        port (int): Port number
        timeout (float): Communication timeout
        update_cycle (float): Update cycle
        bit_addresses: (list[BitAddress]): List of bit address settings
        word_addresses: (list[WordAddress]): List of word address settings
        heartbeat_addresses: (list[CycleBitAddress]): List of heartbeat address settings
    """
    enable: bool = True
    name: str = ""
    location: list[float] = dataclasses.field(default_factory=lambda: [0.0, 0.0])
    interface: str = "Dummy"
    ip: str = "0.0.0.0"
    port: int = 80
    timeout: float = 1.0
    update_cycle: float = 1.0
    bit_addresses: list[BitAddress] = dataclasses.field(default_factory=list)
    word_addresses: list[WordAddress] = dataclasses.field(default_factory=list)
    heartbeat_addresses: list[CycleBitAddress] = dataclasses.field(default_factory=list)

    @classmethod
    def make_form(cls):
        """Create the settings form
        Returns:
            dict: Settings form
        """
        return {
            "enable": {
                "type": "switch",
                "label": "有効",
            },
            "name": {
                "type": "text",
                "label": "名前",
            },
            "location": {
                "type": "location",
                "label": "位置",
            },
            "interface": {
                "type": "select",
                "label": "インターフェース",
                "items": {name: name for name, _ in inspect.getmembers(equipment.plc.access, inspect.isclass)},
            },
            "ip": {
                "type": "text",
                "label": "IPアドレス",
            },
            "port": {
                "type": "number",
                "label": "ポート番号",
                "integer": True,
                "min": 0,
                "max": 65535,
            },
            "timeout": {
                "type": "number",
                "label": "通信タイムアウト",
                "suffix": "秒",
                "min": 0,
            },
            "bit_addresses": {
                "type": "table",
                "label": "ビットアドレス設定",
                "default": dataclasses.asdict(BitAddress()),
                "forms": BitAddress.make_form(),
                "width": 800,
            },
            "word_addresses": {
                "type": "table",
                "label": "ワードアドレス設定",
                "default": dataclasses.asdict(WordAddress()),
                "forms": WordAddress.make_form(),
                "width": 800,
            },
            "heartbeat_addresses": {
                "type": "table",
                "label": "ハートビート設定",
                "default": dataclasses.asdict(CycleBitAddress()),
                "forms": CycleBitAddress.make_form(),
                "width": 800,
            },
        }

    def __post_init__(self):
        """Post-initialization processing"""
        self.bit_addresses = [BitAddress(**address) for address in self.bit_addresses if address.get("enable", False)]
        self.word_addresses = [WordAddress(**address) for address in self.word_addresses if address.get("enable", False)]
        self.heartbeat_addresses = [CycleBitAddress(**address) for address in self.heartbeat_addresses if address.get("enable", False)]


@dataclasses.dataclass
class Domain(abstract.Domain):
    """PLC domain
    Attributes:
        node_domain (list[NodeDomain]): List of node settings
    """
    node_domain:list[NodeDomain] = dataclasses.field(default_factory=list)

    @classmethod
    def make_form(cls):
        """Create the settings form
        Returns:
            dict: Settings form
        """
        return {
            "node_domain": {
                "type": "node",
                "label": "ノード設定",
                "default": dataclasses.asdict(NodeDomain()),
                "forms": NodeDomain.make_form(),
                "unique": ["name"],
                "columns": 1
            }
        }

    def __post_init__(self):
        """Post-initialization processing"""
        self.node_domain = [NodeDomain(**node_domain) for node_domain in self.node_domain if node_domain.get("enable", False)]
