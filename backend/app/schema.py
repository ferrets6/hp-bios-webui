"""
Static menu layout mimicking the real HP F10 "Computer Setup" BIOS UI
for this specific machine (HP ProDesk 400 G5 MT, BIOS Q03).

Categorization is based on HP's own "HP PC Commercial BIOS (UEFI) Setup
Administration Guide" (919946-003), mapped onto the actual attribute
names exposed by the kernel's hp-bioscfg sysfs driver on this box.

Any attribute discovered on the live system that isn't listed here is
placed automatically into "Advanced -> Other" so nothing is ever hidden.
"""

# Attributes that are one-shot actions (buttons), not persistent settings.
ACTION_ATTRIBUTES = {
    "Save Custom Defaults",
    "Apply Custom Defaults and Exit",
    "Apply Factory Defaults and Exit",
    "Clear TPM",
    "Clear Secure Boot keys",
    "Reset Secure Boot keys to factory defaults",
    "Clear BIOS Event Log",
    "Import Custom Secure Boot keys",
    "Ready BIOS for Device Guard Use",
}

# Attributes that are purely informational (read-only in the real BIOS too).
READ_ONLY_HINTS = {
    "Product Name", "Product Family", "SKU Number", "Serial Number",
    "Universally Unique Identifier (UUID)", "Born On Date", "System Board ID",
    "System Board CT Number", "BIOS Build Version", "Build ID",
    "System BIOS Version", "Minimum BIOS Version", "Feature Byte",
    "Processor 1 Type", "Processor 1 Speed", "Processor 1 Cores",
    "Processor 1 Cache Size (L1!L2!L3)", "Processor 1 Stepping",
    "Processor 1 MicroCode Revision", "Processor 1 DIMM1", "Processor 1 DIMM3",
    "Memory Size", "ME Firmware Mode", "ME Firmware Version",
    "Reference Code Revision", "Super I!O Firmware Version",
    "Video BIOS Version", "Storage Devices", "Integrated MAC Address 1",
    "HP Application Driver", "Secure Erase Completion Date",
    "Secure Erase Completion Status", "Secure Erase Hard Disk Model Number",
    "Secure Erase Hard Disk Serial Number", "Custom Keys Image Verification State",
    "USB Type-C Controller(s) Firmware Version:",
}

# tab -> [(subsection title, [attribute names...]), ...]
SECTIONS = {
    "Main": [
        ("System Information", [
            "Product Name", "Product Family", "SKU Number", "Serial Number",
            "Universally Unique Identifier (UUID)", "Born On Date",
            "System Board ID", "System Board CT Number", "BIOS Build Version",
            "Build ID", "System BIOS Version", "Minimum BIOS Version",
            "Feature Byte", "Processor 1 Type", "Processor 1 Speed",
            "Processor 1 Cores", "Processor 1 Cache Size (L1!L2!L3)",
            "Processor 1 Stepping", "Processor 1 MicroCode Revision",
            "Processor 1 DIMM1", "Processor 1 DIMM3", "Memory Size",
            "ME Firmware Mode", "ME Firmware Version", "Reference Code Revision",
            "Super I!O Firmware Version", "Video BIOS Version",
            "Storage Devices", "Integrated MAC Address 1", "HP Application Driver",
        ]),
        ("System IDs", ["Asset Tracking Number", "Ownership Tag"]),
        ("Update System BIOS", [
            "BIOS Rollback Policy", "Automatic BIOS Update Setting",
            "Automatically Check for Updates", "Force Check on Reboot",
            "Update BIOS via Network", "Update Source", "Update Address",
            "Use Proxy", "Proxy Address", "IPv4 Configuration", "IPv4 Address",
            "IPv4 Subnet Mask", "IPv4 Gateway", "DNS Configuration",
            "DNS Addresses", "Data transfer timeout", "Force HTTP no-cache",
            "Force Default IP Configuration", "Clear BIOS Event Log",
        ]),
        ("Manufacturing", ["Custom Logo", "MS Digital Marker", "Manufacturing Programming Mode"]),
        ("Save / Restore Defaults", [
            "Save Custom Defaults", "Apply Custom Defaults and Exit",
            "Apply Factory Defaults and Exit",
        ]),
    ],
    "Security": [
        ("Administrator Tools", [
            "BIOS Administrator visible at Power-on Authentication",
        ]),
        ("Password Policies", [
            "Password Minimum Length",
            "At least one symbol is required in Administrator and User passwords",
            "At least one number is required in Administrator and User passwords",
            "At least one upper case character is required in Administrator and User passwords",
            "At least one lower case character is required in Administrator and User passwords",
            "Are spaces allowed in Administrator and User passwords?",
            "Clear password jumper",
            "Prompt for Admin password on F9 (Boot Menu)",
            "Prompt for Admin password on F11 (System Recovery)",
            "Prompt for Admin password on F12 (Network Boot)",
            "Prompt for Admin password on Capsule Update",
        ]),
        ("Trusted Platform Module (TPM)", [
            "TPM Device", "TPM State", "TPM Specification Version",
            "Clear TPM", "TPM Activation Policy",
        ]),
        ("BIOS Sure Start", ["Sure_Start", "SureStart Production Mode"]),
        ("Security Configuration", [
            "Physical Presence Interface",
            "Intel Software Guard Extensions (SGX)",
            "System Management Command",
        ]),
        ("Absolute Persistence Module", [
            "Absolute Persistence Module Current State",
            "Permanent Disable Absolute Persistence Module Set Once",
        ]),
        ("Hard Drive Utilities", [
            "Save!Restore MBR of System Hard Drive",
            "Save!Restore GPT of System Hard Drive",
            "Boot Sector (MBR!GPT) Recovery Policy",
            "Allow OPAL Hard Drive SID Authentication",
            "Secure Erase Completion Date", "Secure Erase Completion Status",
            "Secure Erase Hard Disk Model Number", "Secure Erase Hard Disk Serial Number",
        ]),
    ],
    "Advanced": [
        ("Display Language", ["Select Language", "Select Keyboard Layout"]),
        ("Scheduled Power-On", [
            "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday",
            "BIOS Power-On Hour", "BIOS Power-On Minute",
        ]),
        ("Boot Options", [
            "Fast Boot", "CD-ROM Boot", "USB Storage Boot", "Network (PXE) Boot",
            "After Power Loss", "UEFI Boot Options", "UEFI Boot Order",
            "Legacy Boot Options", "Legacy Boot Order",
            "HP_Disk0MapForLegacyBootOrder", "HP_Disk0MapForUefiBootOrder",
            "NumLock on at boot", "Startup Delay (sec.)", "Audio Alerts During Boot",
            "Prompt on Fixed Storage Change", "Prompt on Memory Size Change",
        ]),
        ("Secure Boot Configuration", [
            "Configure Legacy Support and Secure Boot", "Import Custom Secure Boot keys",
            "Clear Secure Boot keys", "Reset Secure Boot keys to factory defaults",
            "Enable MS UEFI CA key", "Ready to disable MS UEFI CA Key",
            "Custom Keys Image Verification State", "Ready BIOS for Device Guard Use",
        ]),
        ("System Options", [
            "Multi-processor", "Turbo-boost", "Virtualization Technology (VTx)",
            "Virtualization Technology for Directed I!O (VTd)",
            "PCI Express x1 Slot 1", "PCI Express x1 Slot 2", "PCI Express x16 Slot 1",
            "Allow PCIe!PCI SERR# Interrupt", "Power Button Override",
            "Configure Storage Controller for Intel Optane",
        ]),
        ("Built-in Device Options", [
            "Embedded LAN controller", "Wake On LAN", "Audio Controller",
            "Audio Device", "Internal Speakers", "Microphone", "M.2 SSD",
            "M.2 WLAN!BT", "M.2 USB ! Bluetooth", "Video Memory Size",
            "Dust Filter", "Dust Filter Reminder (Days)",
            "Increase Idle Fan Speed(%)", "Media Card Reader!SD_RDR USB",
        ]),
        ("Port Options", [
            "Front USB Port 1", "Front USB Port 2", "Front USB Ports",
            "Rear USB Port 1", "Rear USB Port 2", "Rear USB Port 3",
            "Rear USB Port 4", "Rear USB Port 5", "Rear USB Port 6", "Rear USB Ports",
            "SATA0", "SATA1", "SATA2", "Restrict USB Devices",
            "USB Type-C Controller(s) Firmware Version:",
        ]),
        ("Option ROM Launch Policy", ["Configure Option ROM Launch Policy"]),
        ("Power Management Options", [
            "Runtime Power Management", "Extended Idle Power States",
            "S5 Maximum Power Savings", "SATA Power Management",
            "PCI Express Power Management", "Power On from Keyboard Ports",
            "Unique Sleep State Blink Rates",
        ]),
        ("Remote HP PC Hardware Diagnostics", [
            "Remote HP PC Hardware Diagnostics Custom Client Download Url",
            "Remote HP PC Hardware Diagnostics Custom Client Upload Url",
            "Remote HP PC Hardware Diagnostics Execute On Next Boot",
            "Remote HP PC Hardware Diagnostics Last Execution Status",
            "Remote HP PC Hardware Diagnostics Last Execution Time Stamp",
            "Remote HP PC Hardware Diagnostics Scheduled Execution Enabled",
            "Remote HP PC Hardware Diagnostics Scheduled Execution Frequency",
            "Remote HP PC Hardware Diagnostics Upload Server Password",
            "Remote HP PC Hardware Diagnostics Upload Server Username",
            "Remote HP PC Hardware Diagnostics Use Custom Download Url",
        ]),
    ],
}

# Roles exposed under .../authentication/ (handled via a dedicated endpoint,
# not through the generic attribute read/write path).
PASSWORD_ROLES = ["Setup Password", "Power-On Password"]

BOOLEAN_PAIRS = {
    frozenset(["Enable", "Disable"]),
    frozenset(["Enabled", "Disabled"]),
    frozenset(["Checked", "Unchecked"]),
    frozenset(["Yes", "No"]),
    frozenset(["On", "Off"]),
}


def widget_for(attr_type: str, possible_values: list[str]) -> str:
    """Decide how the frontend should render this setting."""
    if attr_type == "enumeration":
        if len(possible_values) == 2 and frozenset(possible_values) in BOOLEAN_PAIRS:
            return "toggle"
        return "select"
    if attr_type == "integer":
        return "number"
    return "text"


def flatten_known_names() -> set[str]:
    names: set[str] = set()
    for subsections in SECTIONS.values():
        for _title, attrs in subsections:
            names.update(attrs)
    return names
