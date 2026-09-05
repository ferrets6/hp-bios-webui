"""
Talks to the real BIOS config interface, which lives on the NAS host
(kernel hp-bioscfg sysfs driver at
/sys/class/firmware-attributes/hp-bioscfg/), not on this container.

Reads need no privilege (the sysfs files are world-readable). Writes and
reboot go through a small root-owned wrapper script on the NAS
(installed by deploy/nas_setup.sh) invoked via a scoped NOPASSWD sudoers
rule, so this container never needs a root password.
"""
import os
import shlex
import threading

import paramiko

NAS_HOST = os.environ["NAS_HOST"]
NAS_USER = os.environ["NAS_USER"]
NAS_PORT = int(os.environ.get("NAS_SSH_PORT", "22"))
NAS_KEY_PATH = os.environ["NAS_SSH_KEY_PATH"]
CTL_PATH = os.environ["NAS_CTL_PATH"]

ATTR_DIR = "/sys/class/firmware-attributes/hp-bioscfg/attributes"
AUTH_DIR = "/sys/class/firmware-attributes/hp-bioscfg/authentication"

FIELD_SEP = "\x01"
RECORD_SEP = "\x02"

_lock = threading.Lock()
_client: paramiko.SSHClient | None = None


class NasError(RuntimeError):
    pass


def _connect() -> paramiko.SSHClient:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=NAS_HOST,
        port=NAS_PORT,
        username=NAS_USER,
        key_filename=NAS_KEY_PATH,
        timeout=8,
        banner_timeout=8,
        auth_timeout=8,
    )
    return client


def _get_client() -> paramiko.SSHClient:
    global _client
    with _lock:
        if _client is not None:
            transport = _client.get_transport()
            if transport is not None and transport.is_active():
                return _client
        _client = _connect()
        return _client


def _run(command: str, timeout: int = 15) -> tuple[int, str, str]:
    client = _get_client()
    try:
        _stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
        exit_code = stdout.channel.recv_exit_status()
        out = stdout.read().decode("utf-8", errors="replace")
        err = stderr.read().decode("utf-8", errors="replace")
        return exit_code, out, err
    except (paramiko.SSHException, OSError) as exc:
        global _client
        with _lock:
            _client = None
        raise NasError(f"SSH connection to NAS failed: {exc}") from exc


def read_all_attributes() -> dict:
    """Dump every attribute's display name, type, current value and
    possible values in one round trip."""
    cmd = (
        f'cd "{ATTR_DIR}" && for d in */; do '
        'd="${d%/}"; '
        'printf "%s\\x01%s\\x01%s\\x01%s\\x02" '
        '"$d" "$(cat "$d/type" 2>/dev/null)" '
        '"$(cat "$d/current_value" 2>/dev/null)" '
        '"$(cat "$d/possible_values" 2>/dev/null)"; '
        "done"
    )
    exit_code, out, err = _run(cmd)
    if exit_code != 0 and not out:
        raise NasError(f"failed to list attributes: {err.strip()}")

    attrs = {}
    for record in out.split(RECORD_SEP):
        if not record:
            continue
        parts = record.split(FIELD_SEP)
        if len(parts) != 4:
            continue
        name, attr_type, current_value, possible_values_raw = parts
        possible_values = [v for v in possible_values_raw.split(";") if v != ""]
        attrs[name] = {
            "name": name,
            "type": attr_type,
            "current_value": current_value,
            "possible_values": possible_values,
        }
    return attrs


def read_pending_reboot() -> bool:
    exit_code, out, _err = _run(
        'cat "/sys/class/firmware-attributes/hp-bioscfg/attributes/pending_reboot" 2>/dev/null'
    )
    return exit_code == 0 and out.strip() not in ("", "0")


def read_password_status() -> dict:
    """Read is_enabled for each password role, without needing sudo."""
    result = {}
    for role in ("Setup Password", "Power-On Password"):
        path = shlex.quote(f"{AUTH_DIR}/{role}/is_enabled")
        exit_code, out, _err = _run(f"cat {path} 2>/dev/null")
        result[role] = out.strip() == "1" if exit_code == 0 else None
    return result


def write_attribute(name: str, value: str) -> None:
    remote_cmd = (
        f"sudo {shlex.quote(CTL_PATH)} write-attr {shlex.quote(name)} {shlex.quote(value)}"
    )
    exit_code, _out, err = _run(remote_cmd)
    if exit_code != 0:
        raise NasError(err.strip() or f"failed to write '{name}'")


def set_password(role: str, new_password: str, current_password: str = "") -> None:
    args = [shlex.quote(role), shlex.quote(new_password)]
    if current_password:
        args.append(shlex.quote(current_password))
    remote_cmd = f"sudo {shlex.quote(CTL_PATH)} set-password {' '.join(args)}"
    exit_code, _out, err = _run(remote_cmd)
    if exit_code != 0:
        raise NasError(err.strip() or f"failed to set password for '{role}'")


def reboot() -> None:
    remote_cmd = f"sudo {shlex.quote(CTL_PATH)} reboot"
    _run(remote_cmd, timeout=5)
