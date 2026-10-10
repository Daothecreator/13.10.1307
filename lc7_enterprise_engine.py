#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LC7 Enterprise Audit & Remediation Engine
Монолитное ядро аудита парольной политики, безопасного извлечения хэшей,
оркестрации JtR, автоматического исправления учетных записей и формирования отчетов.
"""

import argparse
import asyncio
import csv
from datetime import datetime, timezone
import importlib.util
import json
import logging
import os
from pathlib import Path
import re
import sqlite3
import sys
import tempfile
from typing import Any, Callable, Dict, List, Optional, Tuple
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, IntEnum, auto

import asyncssh
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.serialization import load_pem_public_key
import keyring

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger("LC7Core")


# ============================================================================
# 1. СЕЙФ УЧЕТНЫХ ДАННЫХ (CREDENTIAL VAULT - AES-256-GCM)
# ============================================================================

VAULT_SERVICE_NAME = "LC7_Enterprise_Vault"
VAULT_KEY_IDENTIFIER = "MasterKey_AES256"


class CredentialVault:
    """Криптографический сейф учетных записей с хранением мастер-ключа в OS Keyring."""

    def __init__(self, db_path: Path):
        self.db_path = str(db_path)
        self._key = self._get_or_create_master_key()
        self._init_db()

    def _get_or_create_master_key(self) -> bytes:
        stored_key = None
        try:
            stored_key = keyring.get_password(VAULT_SERVICE_NAME, VAULT_KEY_IDENTIFIER)
        except Exception:
            try:
                import keyrings.alt.file
                keyring.set_keyring(keyrings.alt.file.EncryptedKeyring())
                stored_key = keyring.get_password(VAULT_SERVICE_NAME, VAULT_KEY_IDENTIFIER)
            except Exception:
                pass

        if stored_key:
            return bytes.fromhex(stored_key)

        key_file = Path(".vault_master.key")
        if key_file.exists():
            return key_file.read_bytes()

        new_key = AESGCM.generate_key(bit_length=256)
        try:
            keyring.set_password(VAULT_SERVICE_NAME, VAULT_KEY_IDENTIFIER, new_key.hex())
        except Exception:
            key_file.write_bytes(new_key)
        return new_key

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS credentials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scope_type TEXT NOT NULL CHECK(scope_type IN ('default', 'host')),
                    protocol TEXT NOT NULL,
                    host TEXT,
                    port INTEGER,
                    username TEXT NOT NULL,
                    auth_type TEXT NOT NULL CHECK(auth_type IN ('password', 'ssh_key')),
                    nonce BLOB NOT NULL,
                    tag BLOB NOT NULL,
                    ciphertext BLOB NOT NULL,
                    UNIQUE(protocol, host, port, username)
                )
            """)

    def store_credential(
        self,
        protocol: str,
        username: str,
        secret: str,
        auth_type: str = "password",
        host: Optional[str] = None,
        port: Optional[int] = 22,
        elevation_secret: Optional[str] = None,
        is_default: bool = False
    ):
        scope_type = "default" if is_default else "host"
        payload = json.dumps({"secret": secret, "elevation_secret": elevation_secret}).encode("utf-8")

        aesgcm = AESGCM(self._key)
        nonce = os.urandom(12)
        encrypted = aesgcm.encrypt(nonce, payload, None)
        ciphertext = encrypted[:-16]
        tag = encrypted[-16:]

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO credentials
                (scope_type, protocol, host, port, username, auth_type, nonce, tag, ciphertext)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (scope_type, protocol, host, port, username, auth_type, nonce, tag, ciphertext))
        logger.info(f"Credential stored successfully for {username}@{host or 'DEFAULT'} [{protocol}]")

    def retrieve_credential(self, protocol: str, host: Optional[str], port: Optional[int] = 22) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM credentials
                WHERE protocol = ? AND host = ? AND port = ? AND scope_type = 'host'
            """, (protocol, host, port))
            row = cursor.fetchone()

            if not row:
                cursor = conn.execute("""
                    SELECT * FROM credentials
                    WHERE protocol = ? AND scope_type = 'default'
                """, (protocol,))
                row = cursor.fetchone()

        if not row:
            return None

        aesgcm = AESGCM(self._key)
        combined_ct = bytes(row["ciphertext"]) + bytes(row["tag"])
        decrypted_bytes = aesgcm.decrypt(bytes(row["nonce"]), combined_ct, None)
        secrets = json.loads(decrypted_bytes.decode("utf-8"))

        return {
            "username": row["username"],
            "auth_type": row["auth_type"],
            "secret": secrets["secret"],
            "elevation_secret": secrets.get("elevation_secret")
        }


# ============================================================================
# 2. АСИНХРОННЫЙ СУПЕРВИЗОР JOHN THE RIPPER (IPC / POT MONITOR)
# ============================================================================

STATUS_REGEX = re.compile(
    r"^(?P<guesses>\d+)g\s+"
    r"(?P<time>\d+:\d{2}:\d{2}:\d{2})\s+"
    r"(?P<progress>[\d\.]+)%\s+"
    r"(\(ETA\s+(?P<eta>[^\)]+)\)\s+)?"
    r"(?P<gps>[\d\.]+[kKMGT]?g/s)\s+"
    r"(?P<pps>[\d\.]+[kKMGT]?p/s)\s+"
    r"(?P<cps>[\d\.]+[kKMGT]?c/s)\s+"
    r"(?P<candidates>.*)$"
)


@dataclass
class JtRStatus:
    guesses: int
    elapsed: str
    progress: float
    eta: Optional[str]
    guesses_per_sec: str
    passwords_per_sec: str
    combinations_per_sec: str
    current_candidates: str


class JtRSupervisor:
    def __init__(
        self,
        john_binary: str,
        session_name: str,
        pot_path: Path,
        on_status: Optional[Callable[[JtRStatus], None]] = None,
        on_cracked: Optional[Callable[[str, str], None]] = None,
    ):
        self.john_binary = john_binary
        self.session_name = session_name
        self.pot_path = pot_path
        self.on_status = on_status
        self.on_cracked = on_cracked
        self._process: Optional[asyncio.subprocess.Process] = None
        self._tasks: List[asyncio.Task] = []
        self._is_running = False

    async def execute(self, extra_args: List[str], poll_interval: float = 2.0):
        cmd = [
            self.john_binary,
            f"--session={self.session_name}",
            f"--pot={self.pot_path}",
            "--crack-status",
            *extra_args,
        ]

        creation_flags = 0
        preexec_fn = None
        if sys.platform == "win32":
            import subprocess
            creation_flags = subprocess.IDLE_PRIORITY_CLASS
        else:
            preexec_fn = lambda: os.nice(19)

        self._process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            creationflags=creation_flags,
            preexec_fn=preexec_fn,
        )

        self._is_running = True
        self._tasks = [
            asyncio.create_task(self._stream_stderr()),
            asyncio.create_task(self._watch_potfile()),
            asyncio.create_task(self._heartbeat(poll_interval)),
        ]

        await self._process.wait()
        self._is_running = False

        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)

    async def _heartbeat(self, interval: float):
        while self._is_running and self._process and self._process.stdin:
            await asyncio.sleep(interval)
            try:
                self._process.stdin.write(b"\n")
                await self._process.stdin.drain()
            except (BrokenPipeError, ConnectionResetError):
                break

    async def _stream_stderr(self):
        while self._is_running and self._process and self._process.stderr:
            line_bytes = await self._process.stderr.readline()
            if not line_bytes:
                break
            line = line_bytes.decode(errors="ignore").strip()
            match = STATUS_REGEX.match(line)
            if match and self.on_status:
                data = match.groupdict()
                status = JtRStatus(
                    guesses=int(data["guesses"]),
                    elapsed=data["time"],
                    progress=float(data["progress"]),
                    eta=data["eta"],
                    guesses_per_sec=data["gps"],
                    passwords_per_sec=data["pps"],
                    combinations_per_sec=data["cps"],
                    current_candidates=data["candidates"].strip(),
                )
                self.on_status(status)

    async def _watch_potfile(self):
        last_offset = self.pot_path.stat().st_size if self.pot_path.exists() else 0
        while self._is_running:
            await asyncio.sleep(0.5)
            if not self.pot_path.exists():
                continue
            current_size = self.pot_path.stat().st_size
            if current_size > last_offset:
                with open(self.pot_path, "r", encoding="utf-8", errors="ignore") as f:
                    f.seek(last_offset)
                    for line in f:
                        line = line.rstrip("\r\n")
                        if not line or line.startswith("#"):
                            continue
                        if ":" in line:
                            ciphertext, plaintext = line.split(":", 1)
                            if self.on_cracked:
                                self.on_cracked(ciphertext, plaintext)
                    last_offset = f.tell()

    async def stop(self):
        if not self._process or self._process.returncode is not None:
            return
        try:
            if self._process.stdin:
                self._process.stdin.write(b"q\n")
                await self._process.stdin.drain()
            await asyncio.wait_for(self._process.wait(), timeout=5.0)
        except (asyncio.TimeoutError, BrokenPipeError):
            self._process.terminate()
            await self._process.wait()


# ============================================================================
# 3. ЭКСТРАКЦИЯ УЧЕТНЫХ ЗАПИСЕЙ UNIX (IN-MEMORY SSH / UNSHADOW)
# ============================================================================

class UnixSSHExtractor:
    def __init__(self, host: str, port: int, creds: Dict[str, Any]):
        self.host = host
        self.port = port
        self.creds = creds

    async def _execute_with_elevation(
        self,
        conn: asyncssh.SSHClientConnection,
        command: str,
        elevation_method: str = "none"
    ) -> str:
        elev_pass = self.creds.get("elevation_secret") or self.creds.get("secret")

        if elevation_method == "sudo":
            full_cmd = f"sudo -S -p '' {command}"
            process = await conn.create_process(full_cmd, stdin=asyncio.subprocess.PIPE)
            stdout, stderr = await process.communicate(input=f"{elev_pass}\n")
            if process.exit_status != 0:
                raise PermissionError(f"Sudo command failure: {stderr.strip()}")
            return stdout
        elif elevation_method == "su":
            full_cmd = f"su -c '{command}' root"
            process = await conn.create_process(full_cmd, stdin=asyncio.subprocess.PIPE)
            stdout, stderr = await process.communicate(input=f"{elev_pass}\n")
            if process.exit_status != 0:
                raise PermissionError(f"Su command failure: {stderr.strip()}")
            return stdout
        else:
            result = await conn.run(command, check=True)
            return result.stdout

    def _unshadow(self, passwd_content: str, shadow_content: str) -> List[str]:
        shadow_map = {}
        for line in shadow_content.splitlines():
            parts = line.strip().split(":")
            if len(parts) >= 2:
                user, hash_val = parts[0], parts[1]
                if hash_val and hash_val not in ("*", "!", "!!", "x", "LK", "NP", "*LK*"):
                    shadow_map[user] = hash_val

        unshadowed = []
        for line in passwd_content.splitlines():
            parts = line.strip().split(":")
            if len(parts) >= 7:
                user = parts[0]
                if user in shadow_map:
                    parts[1] = shadow_map[user]
                    unshadowed.append(":".join(parts))
        return unshadowed

    async def extract_hashes(self, elevation_method: str = "none") -> List[str]:
        client_keys = None
        password = None

        if self.creds["auth_type"] == "ssh_key":
            client_keys = [asyncssh.import_private_key(self.creds["secret"])]
        else:
            password = self.creds["secret"]

        async with asyncssh.connect(
            self.host,
            port=self.port,
            username=self.creds["username"],
            password=password,
            client_keys=client_keys,
            known_hosts=None
        ) as conn:
            passwd_res = await conn.run("cat /etc/passwd", check=True)
            shadow_content = await self._execute_with_elevation(
                conn, "cat /etc/shadow", elevation_method=elevation_method
            )
            return self._unshadow(passwd_res.stdout, shadow_content)


# ============================================================================
# 4. ПОДСИСТЕМА ИСПРАВЛЕНИЯ (CROSS-PLATFORM REMEDIATION)
# ============================================================================

class UnixFlavor(IntEnum):
    LINUX = auto()
    FREEBSD = auto()
    OPENBSD = auto()
    SOLARIS = auto()
    AIX = auto()
    UNKNOWN = auto()


class RemediationAction(IntEnum):
    DISABLE = 1
    FORCE_PASSWORD_CHANGE = 2
    LOCK = 3


@dataclass
class TargetAccount:
    username: str
    uid: Optional[int] = None


@dataclass
class ExecutionResult:
    username: str
    action: RemediationAction
    success: bool
    error_message: Optional[str] = None


class UnixRemediationProvider:
    def __init__(self, host: str, port: int = 22):
        self.host = host
        self.port = port
        self.os_flavor: UnixFlavor = UnixFlavor.UNKNOWN
        self._conn: Optional[asyncssh.SSHClientConnection] = None
        self._sudo_password: Optional[str] = None

    async def connect(
        self,
        username: str,
        password: Optional[str] = None,
        client_keys: Optional[List[Any]] = None,
        sudo_password: Optional[str] = None
    ):
        self._sudo_password = sudo_password or password
        self._conn = await asyncssh.connect(
            self.host,
            port=self.port,
            username=username,
            password=password,
            client_keys=client_keys,
            known_hosts=None
        )
        self.os_flavor = await self._detect_os()

    async def _detect_os(self) -> UnixFlavor:
        result = await self._conn.run("uname -s", check=True)
        name = result.stdout.strip()
        if "Linux" in name:
            return UnixFlavor.LINUX
        elif "FreeBSD" in name:
            return UnixFlavor.FREEBSD
        elif "OpenBSD" in name:
            return UnixFlavor.OPENBSD
        elif "SunOS" in name:
            return UnixFlavor.SOLARIS
        elif "AIX" in name:
            return UnixFlavor.AIX
        return UnixFlavor.UNKNOWN

    def _resolve_command(self, action: RemediationAction, username: str) -> str:
        matrix: Dict[UnixFlavor, Dict[RemediationAction, str]] = {
            UnixFlavor.LINUX: {
                RemediationAction.DISABLE: f"usermod -L {username}",
                RemediationAction.FORCE_PASSWORD_CHANGE: f"chage -d 0 {username}",
                RemediationAction.LOCK: f"passwd -l {username}",
            },
            UnixFlavor.FREEBSD: {
                RemediationAction.DISABLE: f"pw lock {username}",
                RemediationAction.FORCE_PASSWORD_CHANGE: f"pw user mod {username} -p 01-Jan-1970",
                RemediationAction.LOCK: f"pw lock {username}",
            },
            UnixFlavor.OPENBSD: {
                RemediationAction.DISABLE: f"usermod -s /sbin/nologin {username}",
                RemediationAction.FORCE_PASSWORD_CHANGE: f"chpass -e 0 {username}",
                RemediationAction.LOCK: f"passwd -l {username}",
            },
            UnixFlavor.SOLARIS: {
                RemediationAction.DISABLE: f"passwd -l {username}",
                RemediationAction.FORCE_PASSWORD_CHANGE: f"passwd -f {username}",
                RemediationAction.LOCK: f"passwd -l {username}",
            },
            UnixFlavor.AIX: {
                RemediationAction.DISABLE: f'chuser "account_locked=true" {username}',
                RemediationAction.FORCE_PASSWORD_CHANGE: f"pwdadm -f ADMCHG {username}",
                RemediationAction.LOCK: f'chuser "account_locked=true" {username}',
            }
        }
        flavor_commands = matrix.get(self.os_flavor, matrix[UnixFlavor.LINUX])
        if action not in flavor_commands:
            raise NotImplementedError(f"Action {action} unsupported on {self.os_flavor}")
        return flavor_commands[action]

    async def execute_remediation(
        self,
        targets: List[TargetAccount],
        action: RemediationAction,
        use_sudo: bool = True
    ) -> List[ExecutionResult]:
        results = []
        for target in targets:
            cmd = self._resolve_command(action, target.username)
            try:
                if use_sudo and self._sudo_password:
                    full_cmd = f"sudo -S -p '' {cmd}"
                    proc = await self._conn.create_process(full_cmd, stdin=asyncio.subprocess.PIPE)
                    _, stderr = await proc.communicate(input=f"{self._sudo_password}\n")
                    exit_code = proc.exit_status
                else:
                    res = await self._conn.run(cmd)
                    exit_code = res.exit_status
                    stderr = res.stderr

                if exit_code == 0:
                    results.append(ExecutionResult(username=target.username, action=action, success=True))
                else:
                    results.append(ExecutionResult(
                        username=target.username,
                        action=action,
                        success=False,
                        error_message=stderr.strip() or f"Process exited with {exit_code}"
                    ))
            except Exception as e:
                results.append(ExecutionResult(
                    username=target.username,
                    action=action,
                    success=False,
                    error_message=str(e)
                ))
        return results

    async def close(self):
        if self._conn:
            self._conn.close()
            await self._conn.wait_closed()


# ============================================================================
# 5. СИСТЕМА ПЛАГИНОВ (SECURITY & DEPENDENCY RESOLUTION)
# ============================================================================

class PluginSecurityError(Exception):
    pass


class DependencyResolutionError(Exception):
    pass


@dataclass
class PluginManifest:
    plugin_id: str
    name: str
    version: str
    entry_point: str
    dependencies: List[str]
    capabilities: List[str]
    base_path: Path


class PluginSignatureVerifier:
    def __init__(self, vendor_public_key_pem: bytes):
        self._public_key = load_pem_public_key(vendor_public_key_pem)

    def verify_file(self, file_path: Path, signature_path: Path) -> bool:
        if not file_path.exists() or not signature_path.exists():
            return False
        data = file_path.read_bytes()
        signature = signature_path.read_bytes()
        try:
            self._public_key.verify(
                signature,
                data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except InvalidSignature:
            return False


class DependencyGraph:
    def __init__(self, manifests: Dict[str, PluginManifest]):
        self.manifests = manifests

    def resolve_load_order(self) -> List[str]:
        for pid, manifest in self.manifests.items():
            for dep in manifest.dependencies:
                if dep not in self.manifests:
                    raise DependencyResolutionError(f"Missing dependency '{dep}' for plugin '{pid}'.")

        visited: Dict[str, int] = {pid: 0 for pid in self.manifests}
        order: List[str] = []

        def dfs(node: str, path: List[str]):
            visited[node] = 1
            path.append(node)
            for neighbor in self.manifests[node].dependencies:
                if visited[neighbor] == 1:
                    cycle = " -> ".join(path[path.index(neighbor):] + [neighbor])
                    raise DependencyResolutionError(f"Cyclic dependency detected: {cycle}")
                if visited[neighbor] == 0:
                    dfs(neighbor, path)
            path.pop()
            visited[node] = 2
            order.append(node)

        for pid in self.manifests:
            if visited[pid] == 0:
                dfs(pid, [])
        return order


class LC7PluginEngine:
    def __init__(self, plugins_dir: Path, vendor_pubkey_path: Path):
        self.plugins_dir = plugins_dir
        self.verifier = PluginSignatureVerifier(vendor_pubkey_path.read_bytes())
        self.manifests: Dict[str, PluginManifest] = {}
        self.loaded_modules: Dict[str, Any] = {}
        self.load_order: List[str] = []

    def discover_and_validate(self):
        for manifest_path in self.plugins_dir.glob("*/manifest.json"):
            plugin_folder = manifest_path.parent
            sig_path = manifest_path.with_suffix(".json.sig")

            if not self.verifier.verify_file(manifest_path, sig_path):
                raise PluginSecurityError(f"Invalid signature for manifest: {manifest_path}")

            with open(manifest_path, "r", encoding="utf-8") as f:
                raw = json.load(f)

            manifest = PluginManifest(
                plugin_id=raw["plugin_id"],
                name=raw["name"],
                version=raw["version"],
                entry_point=raw["entry_point"],
                dependencies=raw.get("dependencies", []),
                capabilities=raw.get("provided_capabilities", []),
                base_path=plugin_folder
            )

            entry_file = plugin_folder / manifest.entry_point
            entry_sig = entry_file.with_suffix(entry_file.suffix + ".sig")
            if not self.verifier.verify_file(entry_file, entry_sig):
                raise PluginSecurityError(f"Invalid signature for entry file: {entry_file}")

            self.manifests[manifest.plugin_id] = manifest

        graph = DependencyGraph(self.manifests)
        self.load_order = graph.resolve_load_order()

    def initialize_plugins(self, core_context: Dict[str, Any]):
        for pid in self.load_order:
            manifest = self.manifests[pid]
            entry_path = manifest.base_path / manifest.entry_point
            spec = importlib.util.spec_from_file_location(f"lc7_plugin_{pid}", entry_path)
            if not spec or not spec.loader:
                raise ImportError(f"Cannot load spec for {entry_path}")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, "register_plugin"):
                module.register_plugin(core_context)
            self.loaded_modules[pid] = module


# ============================================================================
# 6. ГЕНЕРАТОР ОТЧЕТОВ (REPORT AST / EXPORTERS: HTML+SVG, XML, CSV)
# ============================================================================

class ElementType(Enum):
    PARAGRAPH = auto()
    METRIC_GRID = auto()
    DATA_TABLE = auto()
    CHART = auto()


@dataclass
class ReportElement(ABC):
    element_type: ElementType


@dataclass
class ParagraphElement(ReportElement):
    text: str
    is_lead: bool = False

    def __init__(self, text: str, is_lead: bool = False):
        super().__init__(ElementType.PARAGRAPH)
        self.text = text
        self.is_lead = is_lead


@dataclass
class MetricItem:
    label: str
    value: str
    delta: Optional[str] = None
    status: str = "normal"


@dataclass
class MetricGridElement(ReportElement):
    metrics: List[MetricItem] = field(default_factory=list)

    def __init__(self, metrics: List[MetricItem]):
        super().__init__(ElementType.METRIC_GRID)
        self.metrics = metrics


@dataclass
class DataTableElement(ReportElement):
    headers: List[str]
    rows: List[List[Any]]
    caption: Optional[str] = None

    def __init__(self, headers: List[str], rows: List[List[Any]], caption: Optional[str] = None):
        super().__init__(ElementType.DATA_TABLE)
        self.headers = headers
        self.rows = rows
        self.caption = caption


@dataclass
class ChartElement(ReportElement):
    chart_type: str
    title: str
    series_data: Dict[str, Any]

    def __init__(self, chart_type: str, title: str, series_data: Dict[str, Any]):
        super().__init__(ElementType.CHART)
        self.chart_type = chart_type
        self.title = title
        self.series_data = series_data


@dataclass
class ReportSection:
    section_id: str
    title: str
    elements: List[ReportElement] = field(default_factory=list)


@dataclass
class ReportDocument:
    report_title: str
    organization: str
    generated_at: str
    session_id: str
    classification: str = "CONFIDENTIAL"
    sections: List[ReportSection] = field(default_factory=list)


class IReportExporter(ABC):
    @abstractmethod
    def export(self, document: ReportDocument, output_path: Path) -> None:
        pass


class CSVExporter(IReportExporter):
    def export(self, document: ReportDocument, output_path: Path) -> None:
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["# REPORT TITLE", document.report_title])
            writer.writerow(["# SESSION ID", document.session_id])
            writer.writerow(["# GENERATED AT", document.generated_at])
            writer.writerow([])
            for section in document.sections:
                writer.writerow([f"=== SECTION: {section.title} ==="])
                for elem in section.elements:
                    if isinstance(elem, MetricGridElement):
                        writer.writerow(["Metric", "Value", "Delta"])
                        for m in elem.metrics:
                            writer.writerow([m.label, m.value, m.delta or ""])
                        writer.writerow([])
                    elif isinstance(elem, DataTableElement):
                        if elem.caption:
                            writer.writerow([f"# Table: {elem.caption}"])
                        writer.writerow(elem.headers)
                        for row in elem.rows:
                            writer.writerow(row)
                        writer.writerow([])


class XMLExporter(IReportExporter):
    def export(self, document: ReportDocument, output_path: Path) -> None:
        root = ET.Element("AuditReport", {
            "sessionId": document.session_id,
            "generatedAt": document.generated_at,
            "classification": document.classification
        })
        title_node = ET.SubElement(root, "Title")
        title_node.text = document.report_title
        sections_node = ET.SubElement(root, "Sections")

        for section in document.sections:
            sec_node = ET.SubElement(sections_node, "Section", {"id": section.section_id, "title": section.title})
            for elem in section.elements:
                if isinstance(elem, MetricGridElement):
                    metrics_node = ET.SubElement(sec_node, "Metrics")
                    for m in elem.metrics:
                        ET.SubElement(metrics_node, "Metric", {"label": m.label, "value": m.value, "status": m.status})
                elif isinstance(elem, DataTableElement):
                    table_node = ET.SubElement(sec_node, "DataTable", {"caption": elem.caption or ""})
                    headers_node = ET.SubElement(table_node, "Headers")
                    for h in elem.headers:
                        ET.SubElement(headers_node, "Header").text = str(h)
                    rows_node = ET.SubElement(table_node, "Rows")
                    for r in elem.rows:
                        row_node = ET.SubElement(rows_node, "Row")
                        for cell in r:
                            ET.SubElement(row_node, "Cell").text = str(cell)
                elif isinstance(elem, ChartElement):
                    chart_node = ET.SubElement(sec_node, "Chart", {"type": elem.chart_type, "title": elem.title})
                    for k, v in elem.series_data.items():
                        ET.SubElement(chart_node, "Point", {"key": str(k), "value": str(v)})

        tree = ET.ElementTree(root)
        tree.write(str(output_path), encoding="utf-8", xml_declaration=True)


class HTMLExporter(IReportExporter):
    def _render_svg_histogram(self, series: Dict[str, Any]) -> str:
        if not series:
            return ""
        max_val = max(series.values()) if series.values() else 1
        svg_bars = []
        x = 10
        for k, v in series.items():
            height = int((v / max_val) * 120) if max_val > 0 else 0
            y = 140 - height
            svg_bars.append(
                f'<rect x="{x}" y="{y}" width="25" height="{height}" fill="#2563eb"/>'
                f'<text x="{x+12}" y="155" font-size="10" text-anchor="middle">{k}</text>'
                f'<text x="{x+12}" y="{y-4}" font-size="9" text-anchor="middle">{v}</text>'
            )
            x += 35
        return f'''<svg width="{x + 20}" height="170" class="report-chart">{"".join(svg_bars)}</svg>'''

    def export(self, document: ReportDocument, output_path: Path) -> None:
        html_parts = [
            f"""<!DOCTYPE html><html><head><meta charset="utf-8">
            <title>{document.report_title}</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; padding: 40px; color: #1e293b; background: #fff; }}
                .metric-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin: 20px 0; }}
                .metric-card {{ border: 1px solid #e2e8f0; border-radius: 6px; padding: 16px; background: #f8fafc; }}
                .metric-card.critical {{ border-left: 4px solid #ef4444; }}
                .metric-card.warning {{ border-left: 4px solid #f59e0b; }}
                .metric-card.success {{ border-left: 4px solid #10b981; }}
                .metric-val {{ font-size: 24px; font-weight: bold; margin-top: 4px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ border: 1px solid #e2e8f0; padding: 10px; text-align: left; }}
                th {{ background: #f1f5f9; font-weight: 600; }}
                .header-band {{ border-bottom: 2px solid #0f172a; padding-bottom: 15px; margin-bottom: 30px; }}
                .lead {{ font-size: 1.15em; color: #334155; }}
            </style></head><body>
            <div class="header-band">
                <h1>{document.report_title}</h1>
                <div><strong>Session:</strong> {document.session_id} | <strong>Generated:</strong> {document.generated_at} | <strong>Classification:</strong> {document.classification}</div>
            </div>"""
        ]

        for section in document.sections:
            html_parts.append(f"<h2>{section.title}</h2>")
            for elem in section.elements:
                if isinstance(elem, ParagraphElement):
                    html_parts.append(f"<p class='{'lead' if elem.is_lead else ''}'>{elem.text}</p>")
                elif isinstance(elem, MetricGridElement):
                    html_parts.append("<div class='metric-grid'>")
                    for m in elem.metrics:
                        html_parts.append(
                            f"<div class='metric-card {m.status}'><div>{m.label}</div><div class='metric-val'>{m.value}</div></div>"
                        )
                    html_parts.append("</div>")
                elif isinstance(elem, DataTableElement):
                    html_parts.append("<table><thead><tr>")
                    for h in elem.headers:
                        html_parts.append(f"<th>{h}</th>")
                    html_parts.append("</tr></thead><tbody>")
                    for row in elem.rows:
                        html_parts.append("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>")
                    html_parts.append("</tbody></table>")
                elif isinstance(elem, ChartElement):
                    html_parts.append(f"<div><h3>{elem.title}</h3>{self._render_svg_histogram(elem.series_data)}</div>")

        html_parts.append("</body></html>")
        output_path.write_text("".join(html_parts), encoding="utf-8")


# ============================================================================
# 7. ЕДИНЫЙ ПАЙПЛАЙН АУДИТА И ИСПРАВЛЕНИЯ (PIPELINE CONTROLLER)
# ============================================================================

class EnterpriseAuditEngine:
    def __init__(self, work_dir: Path, vault_db_path: Path):
        self.work_dir = work_dir
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.vault = CredentialVault(vault_db_path)
        self.exporters: Dict[str, IReportExporter] = {
            "csv": CSVExporter(),
            "xml": XMLExporter(),
            "html": HTMLExporter(),
        }

    async def run_ssh_audit_pipeline(
        self,
        target_host: str,
        john_binary: str,
        wordlist_path: Path,
        session_id: str,
        remediation_policy: Optional[RemediationAction] = None,
        report_format: str = "html",
        report_output_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        creds = self.vault.retrieve_credential("ssh", target_host, port=22)
        if not creds:
            raise ValueError(f"Vault error: Missing credentials for host '{target_host}'.")

        logger.info(f"Connecting via SSH to {target_host} for in-memory extraction...")
        extractor = UnixSSHExtractor(target_host, 22, creds)
        elevation = "sudo" if creds["username"] != "root" else "none"
        unshadowed_hashes = await extractor.extract_hashes(elevation_method=elevation)

        if not unshadowed_hashes:
            logger.warning(f"No crackable user hashes retrieved from {target_host}.")
            return {"status": "empty", "total_accounts": 0}

        pot_file = self.work_dir / f"{session_id}.pot"
        cracked_dict: Dict[str, str] = {}

        def on_cracked(h, p):
            cracked_dict[h] = p
            logger.info(f"[CRACKED] {h} -> {p}")

        def on_status(s: JtRStatus):
            logger.info(f"[{s.elapsed}] {s.progress}% | Rate: {s.combinations_per_sec} | ETA: {s.eta}")

        supervisor = JtRSupervisor(
            john_binary=john_binary,
            session_name=session_id,
            pot_path=pot_file,
            on_status=on_status,
            on_cracked=on_cracked,
        )

        with tempfile.NamedTemporaryFile(mode="w+", delete=True, encoding="utf-8") as tmp_hash:
            tmp_hash.write("\n".join(unshadowed_hashes))
            tmp_hash.flush()

            logger.info(f"Starting John the Ripper (Session: {session_id})...")
            attack_args = [
                "--format=crypt",
                f"--wordlist={wordlist_path}",
                "--rules=Wordlist",
                tmp_hash.name,
            ]
            await supervisor.execute(attack_args)

        remediated_count = 0
        if remediation_policy and cracked_dict:
            logger.info(f"Executing remediation policy {remediation_policy.name} across compromised targets...")
            remediator = UnixRemediationProvider(target_host, 22)
            await remediator.connect(
                username=creds["username"],
                password=creds.get("secret"),
                sudo_password=creds.get("elevation_secret") or creds.get("secret")
            )

            compromised_users = []
            for line in unshadowed_hashes:
                parts = line.split(":")
                u, h = parts[0], parts[1]
                if h in cracked_dict:
                    compromised_users.append(TargetAccount(username=u))

            results = await remediator.execute_remediation(
                compromised_users,
                remediation_policy,
                use_sudo=(creds["username"] != "root")
            )
            await remediator.close()
            remediated_count = sum(1 for r in results if r.success)
            logger.info(f"Remediation finished: {remediated_count}/{len(compromised_users)} successful.")

        if report_output_path:
            timestamp_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            doc = ReportDocument(
                report_title="Enterprise Password Security Audit",
                organization="Security Operations Center",
                generated_at=timestamp_iso,
                session_id=session_id,
                classification="RESTRICTED // SEC-OPS",
            )

            summary_section = ReportSection("exec_summary", "Executive Summary")
            total_accounts = len(unshadowed_hashes)
            cracked_count = len(cracked_dict)
            pct = (cracked_count / total_accounts * 100) if total_accounts > 0 else 0

            summary_section.elements.append(
                ParagraphElement(
                    f"Automated credential audit concluded for host {target_host}. "
                    f"{total_accounts} accounts evaluated; {cracked_count} ({pct:.1f}%) weak credentials identified.",
                    is_lead=True
                )
            )
            summary_section.elements.append(
                MetricGridElement([
                    MetricItem("Accounts Scanned", str(total_accounts)),
                    MetricItem("Compromised", f"{cracked_count} ({pct:.1f}%)", status="critical" if pct > 20 else "warning"),
                    MetricItem("Remediated", str(remediated_count), status="success"),
                    MetricItem("Host", target_host),
                ])
            )

            len_dist: Dict[str, int] = {}
            for pwd in cracked_dict.values():
                bucket = f"Len {len(pwd)}"
                len_dist[bucket] = len_dist.get(bucket, 0) + 1

            if len_dist:
                summary_section.elements.append(
                    ChartElement("histogram", "Cracked Password Length Distribution", len_dist)
                )

            table_rows = []
            for line in unshadowed_hashes:
                parts = line.split(":")
                u = parts[0]
                h = parts[1] if len(parts) > 1 else ""
                status_str = "COMPROMISED" if h in cracked_dict else "SECURE"
                table_rows.append([u, target_host, status_str])

            summary_section.elements.append(
                DataTableElement(
                    headers=["Username", "Host", "Posture"],
                    rows=table_rows,
                    caption="Credential Assessment Inventory"
                )
            )

            doc.sections.append(summary_section)
            exporter = self.exporters.get(report_format.lower(), self.exporters["html"])
            exporter.export(doc, report_output_path)
            logger.info(f"Audit report generated: {report_output_path}")

        return {
            "status": "completed",
            "session_id": session_id,
            "total_accounts": len(unshadowed_hashes),
            "cracked_count": len(cracked_dict),
            "remediated_count": remediated_count
        }


# ============================================================================
# 8. CLI ENTRYPOINT И ЗАПУСК
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="LC7 Enterprise Password Auditing & Remediation Engine")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # vault-add
    p_vault = subparsers.add_parser("vault-add", help="Add credentials to the secure vault")
    p_vault.add_argument("--protocol", default="ssh", help="Protocol (default: ssh)")
    p_vault.add_argument("--host", help="Target host (or omit if using --default)")
    p_vault.add_argument("--port", type=int, default=22, help="Target port (default: 22)")
    p_vault.add_argument("--user", required=True, help="SSH Username")
    p_vault.add_argument("--auth-type", choices=["password", "ssh_key"], default="password")
    p_vault.add_argument("--secret", required=True, help="Password or private key content/path")
    p_vault.add_argument("--sudo-pass", help="Sudo/Elevation password (optional)")
    p_vault.add_argument("--default", action="store_true", help="Set as default credential")
    p_vault.add_argument("--vault-db", default="lc7_vault.db", help="Path to SQLite Vault DB")

    # audit
    p_audit = subparsers.add_parser("audit", help="Run full in-memory SSH audit & remediation pipeline")
    p_audit.add_argument("--host", required=True, help="Target host")
    p_audit.add_argument("--john-bin", default="john", help="Path to john binary")
    p_audit.add_argument("--wordlist", required=True, type=Path, help="Path to wordlist")
    p_audit.add_argument("--session-id", default=f"audit_{int(datetime.now().timestamp())}", help="Session ID")
    p_audit.add_argument("--remediation", choices=["DISABLE", "FORCE_PASSWORD_CHANGE", "LOCK"], help="Remediation policy")
    p_audit.add_argument("--format", choices=["html", "xml", "csv"], default="html", help="Report format")
    p_audit.add_argument("--report-out", type=Path, default=Path("audit_report.html"), help="Report output path")
    p_audit.add_argument("--work-dir", type=Path, default=Path(".lc7_work"), help="Working directory")
    p_audit.add_argument("--vault-db", type=Path, default=Path("lc7_vault.db"), help="Vault DB path")

    # keygen-plugin
    p_keygen = subparsers.add_parser("keygen-plugin", help="Generate RSA-PSS keypair for vendor plugin signing")
    p_keygen.add_argument("--out-dir", type=Path, default=Path("."), help="Directory to save keys")

    args = parser.parse_args()

    if args.command == "vault-add":
        secret_data = args.secret
        if args.auth_type == "ssh_key" and os.path.exists(args.secret):
            secret_data = Path(args.secret).read_text(encoding="utf-8")

        vault = CredentialVault(Path(args.vault_db))
        vault.store_credential(
            protocol=args.protocol,
            username=args.user,
            secret=secret_data,
            auth_type=args.auth_type,
            host=args.host if not args.default else None,
            port=args.port,
            elevation_secret=args.sudo_pass,
            is_default=args.default
        )

    elif args.command == "keygen-plugin":
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        priv_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        pub_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        (args.out_dir / "vendor_plugin_private.pem").write_bytes(priv_pem)
        (args.out_dir / "vendor_plugin_public.pem").write_bytes(pub_pem)
        logger.info(f"Plugin RSA keys generated in {args.out_dir}")

    elif args.command == "audit":
        policy = RemediationAction[args.remediation] if args.remediation else None
        engine = EnterpriseAuditEngine(work_dir=args.work_dir, vault_db_path=args.vault_db)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                engine.run_ssh_audit_pipeline(
                    target_host=args.host,
                    john_binary=args.john_bin,
                    wordlist_path=args.wordlist,
                    session_id=args.session_id,
                    remediation_policy=policy,
                    report_format=args.format,
                    report_output_path=args.report_out
                )
            )
            print("\n" + "=" * 50)
            print("AUDIT PIPELINE COMPLETED")
            print(json.dumps(result, indent=2))
            print("=" * 50)
        finally:
            loop.close()


if __name__ == "__main__":
    main()
