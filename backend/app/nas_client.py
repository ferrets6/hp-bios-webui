"""
Picks the backend that talks to the hp-bioscfg sysfs interface, based on
where this container is deployed:

- NAS_HOST set        -> nas_client_ssh: the target machine is remote
                          (e.g. this container runs on a Raspberry Pi,
                          the BIOS host is a separate NAS). See
                          docker-compose.remote.yml.
- NAS_HOST unset       -> nas_client_local: this container runs directly
                          on the BIOS host, bind-mounting sysfs in. See
                          docker-compose.local.yml (the default).
"""
import os

if os.environ.get("NAS_HOST"):
    from .nas_client_ssh import (
        NasError,
        read_all_attributes,
        read_password_status,
        read_pending_reboot,
        reboot,
        set_password,
        write_attribute,
    )
else:
    from .nas_client_local import (
        NasError,
        read_all_attributes,
        read_password_status,
        read_pending_reboot,
        reboot,
        set_password,
        write_attribute,
    )

__all__ = [
    "NasError",
    "read_all_attributes",
    "read_password_status",
    "read_pending_reboot",
    "reboot",
    "set_password",
    "write_attribute",
]
