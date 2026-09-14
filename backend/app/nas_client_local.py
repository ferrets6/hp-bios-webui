"""
Local-deploy backend: the container runs directly on the machine that has
the hp-bioscfg sysfs interface, so it reads/writes
/sys/class/firmware-attributes/hp-bioscfg/ directly (bind-mounted in, with
the container running privileged - see docker-compose.local.yml).

Reboot is the one operation that has to reach outside the container's own
PID namespace: it uses nsenter to run the host's systemctl inside PID 1's
namespaces (container must run with pid: host for /proc/1 to be the real
host init).

Selected automatically by nas_client.py when NAS_HOST is not set.
"""
import os
import subprocess

ATTR_DIR = "/sys/class/firmware-attributes/hp-bioscfg/attributes"
AUTH_DIR = "/sys/class/firmware-attributes/hp-bioscfg/authentication"

PASSWORD_ROLE_DIRS = {
    "Setup Password": "Setup Password",
    "Power-On Password": "Power-On Password",
}


class NasError(RuntimeError):
    pass


def _read_file(path: str) -> str | None:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read().strip()
    except OSError:
        return None


def _write_file(path: str, value: str) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(value)
    except OSError as exc:
        raise NasError(f"failed to write {path!r}: {exc}") from exc


def read_all_attributes() -> dict:
    """Every attribute's display name, type, current value and possible
    values, read straight from sysfs."""
    try:
        entries = sorted(os.listdir(ATTR_DIR))
    except OSError as exc:
        raise NasError(f"failed to list attributes: {exc}") from exc

    attrs = {}
    for name in entries:
        base = os.path.join(ATTR_DIR, name)
        if not os.path.isdir(base):
            continue
        attr_type = _read_file(os.path.join(base, "type")) or ""
        current_value = _read_file(os.path.join(base, "current_value")) or ""
        possible_values_raw = _read_file(os.path.join(base, "possible_values")) or ""
        possible_values = [v for v in possible_values_raw.split(";") if v != ""]
        attrs[name] = {
            "name": name,
            "type": attr_type,
            "current_value": current_value,
            "possible_values": possible_values,
        }
    return attrs


def read_pending_reboot() -> bool:
    value = _read_file(os.path.join(ATTR_DIR, "pending_reboot"))
    return value is not None and value not in ("", "0")


def read_password_status() -> dict:
    result = {}
    for role, dirname in PASSWORD_ROLE_DIRS.items():
        value = _read_file(os.path.join(AUTH_DIR, dirname, "is_enabled"))
        result[role] = value == "1" if value is not None else None
    return result


def _attribute_dir(name: str) -> str:
    """Resolve `name` to its sysfs directory, rejecting path traversal and
    anything that isn't a real, existing attribute."""
    if not name or "/" in name or "\\" in name or name in (".", ".."):
        raise NasError(f"invalid attribute name: {name!r}")
    base = os.path.join(ATTR_DIR, name)
    if not os.path.isdir(base):
        raise NasError(f"unknown attribute: {name!r}")
    return base


def write_attribute(name: str, value: str) -> None:
    base = _attribute_dir(name)
    _write_file(os.path.join(base, "current_value"), value)


def set_password(role: str, new_password: str, current_password: str = "") -> None:
    dirname = PASSWORD_ROLE_DIRS.get(role)
    if dirname is None:
        raise NasError(f"unknown password role: {role!r}")
    base = os.path.join(AUTH_DIR, dirname)
    if current_password:
        _write_file(os.path.join(base, "current_password"), current_password)
    _write_file(os.path.join(base, "new_password"), new_password)


def reboot() -> None:
    try:
        subprocess.run(
            ["nsenter", "-t", "1", "-m", "-u", "-n", "-i", "-p", "--", "systemctl", "reboot"],
            timeout=5,
            check=True,
            capture_output=True,
        )
    except (subprocess.SubprocessError, OSError) as exc:
        raise NasError(f"failed to trigger reboot: {exc}") from exc
