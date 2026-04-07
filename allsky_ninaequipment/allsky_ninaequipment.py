"""
allsky_ninaequipment.py - v0.2.0

AllSky module to capture N.I.N.A imaging session data via the Advanced API plugin.
Requires the Advanced API plugin v2.2.x installed and enabled in N.I.N.A.
"""

import allsky_shared as s
import json
from urllib.request import urlopen

metaData = {
    "name": "NINA Equipment",
    "description": "Captures N.I.N.A imaging session data via the Advanced API plugin.",
    "module": "allsky_ninaequipment",
    "version": "v0.2.0",
    "events": ["night", "day"],
    "experimental": "true",
    "arguments": {
        "nina_server": "http://192.168.1.28:1888",
        "timeout": "2",
        "log_target": "true",
        "log_filter": "true",
        "log_tracking": "true",
        "log_pier": "true",
        "log_meridian": "true",
        "log_guiding": "true",
        "log_camtemp": "true",
        "log_cooler": "true",
        "log_camstate": "false",
        "log_hfr": "true",
        "log_stars": "false",
        "log_afresult": "false",
        "extradatafilename": "ninaequipment.json"
    },
    "argumentdetails": {
        "nina_server": {
            "required": "true",
            "description": "N.I.N.A Advanced API Server URL",
            "help": "e.g. http://192.168.1.28:1888 , hostname.local is also acceptable in testing."
        },
        "timeout": {
            "required": "false",
            "description": "Request Timeout (seconds)",
            "help": "How long to wait for a response from the N.I.N.A API."
        },
        "log_target": {
            "description": "Log Target Name",
            "help": "Export AS_NINATARGET - current sequence target name.",
            "type": {"fieldtype": "checkbox"}
        },
        "log_filter": {
            "description": "Log Current Filter",
            "help": "Export AS_NINAFILTER - active filter wheel selection.",
            "type": {"fieldtype": "checkbox"}
        },
        "log_tracking": {
            "description": "Log Tracking Mode",
            "help": "Export AS_NINATRACKING - mount tracking mode.",
            "type": {"fieldtype": "checkbox"}
        },
        "log_pier": {
            "description": "Log Pier Side",
            "help": "Export AS_NINAPIER - mount pier side (E or W).",
            "type": {"fieldtype": "checkbox"}
        },
        "log_meridian": {
            "description": "Log Time to Meridian Flip",
            "help": "Export AS_NINAFLIP - hours and minutes until next meridian flip.",
            "type": {"fieldtype": "checkbox"}
        },
        "log_guiding": {
            "description": "Log Guiding State and RMS",
            "help": "Export AS_NINAGUIDE - PHD2 guiding state and RMS error.",
            "type": {"fieldtype": "checkbox"}
        },
        "log_camtemp": {
            "description": "Log Camera Temperature",
            "help": "Export AS_NINACAMTEMP - current camera sensor temperature.",
            "type": {"fieldtype": "checkbox"}
        },
        "log_cooler": {
            "description": "Log Cooler Power",
            "help": "Export AS_NINACOOLER - camera cooler power percentage.",
            "type": {"fieldtype": "checkbox"}
        },
        "log_camstate": {
            "description": "Log Camera State",
            "help": "Export AS_NINACAMSTATE - camera state (Idle, Exposing, etc).",
            "type": {"fieldtype": "checkbox"}
        },
        "log_hfr": {
            "description": "Log Last Frame HFR",
            "help": "Export AS_NINAHFR - HFR value from the most recent captured frame.",
            "type": {"fieldtype": "checkbox"}
        },
        "log_stars": {
            "description": "Log Last Frame Star Count",
            "help": "Export AS_NINASTARS - star count from the most recent captured frame.",
            "type": {"fieldtype": "checkbox"}
        },
        "log_afresult": {
            "description": "Log Last Autofocus Result",
            "help": "Export AS_NINAAFPOS and AS_NINAAFHFR - last autofocus position and HFR.",
            "type": {"fieldtype": "checkbox"}
        },
        "extradatafilename": {
            "required": "false",
            "description": "Extra Data Filename",
            "help": "Filename for overlay data (JSON)."
        }
    },
        "changelog": {
        "v0.1.0": [
            {
                "author": "Jim Cauthen",
                "authorurl": "https://github.com/jcauthen78/",
                "changes": "Initial Release: Basic equipment info and N.I.N.A. connectivity."
            }
        ],
        "v0.2.0": [
            {
                "author": "Jim Cauthen",
                "authorurl": "https://github.com/jcauthen78/",
                "changes": "Expanded equipment data points, added error handling, and improved target detection logic."
            }
        ]
    }
}



def get_nina_json(base_url, endpoint, timeout=2):
    """Fetch JSON from a N.I.N.A Advanced API endpoint. Returns parsed Response or None."""
    url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    try:
        with urlopen(url, timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8"))
            if data.get("Success") and data.get("StatusCode") == 200:
                return data.get("Response")
    except Exception as e:
        s.log(4, f"INFO: allsky_ninaequipment: {endpoint} fetch failed: {e}")
    return None


def is_checked(params, key):
    """Return True if a checkbox param is enabled."""
    return str(params.get(key, "false")).lower() in ("true", "1", "yes")


def find_running_target(sequence_state):
    """
    Walk sequence/state tree to find the RUNNING target container.
    Prefers Target.TargetName directly; falls back to stripping _Container from name.
    """
    if not sequence_state or not isinstance(sequence_state, list):
        return None

    skip_exact = {
        "Targets_Container",
        "Start_Container",
        "End_Container"
    }

    skip_keywords = (
        "EQUIPMENT_CHECK",
        "PREPARE_TARGET",
        "IMAGING",
        "Sequence",
        "END_",
        "START_",
        "Annotation"
    )

    def walk(items):
        if not isinstance(items, list):
            return None
        for item in items:
            if not isinstance(item, dict):
                continue
            name = item.get("Name", "")
            status = item.get("Status", "")
            sub_items = item.get("Items", [])

            if (status == "RUNNING"
                    and name.endswith("_Container")
                    and name not in skip_exact
                    and not any(kw in name for kw in skip_keywords)):
                target_obj = item.get("Target")
                if target_obj and target_obj.get("TargetName"):
                    return target_obj["TargetName"]
                return name.replace("_Container", "").strip()

            result = walk(sub_items)
            if result:
                return result
        return None


def format_meridian(hours_float):
    """Convert decimal hours to HH:MM string."""
    try:
        h = int(hours_float)
        m = int((hours_float - h) * 60)
        return f"{h:02d}:{m:02d}"
    except Exception:
        return "N/A"


def ninaequipment(params, event):
    try:
        server = params.get("nina_server", "").rstrip("/")
        timeout = int(float(params.get("timeout", 2)))
        extrafile = params.get("extradatafilename", "ninaequipment.json")

        need_equip = any(is_checked(params, k) for k in (
            "log_filter", "log_tracking", "log_pier", "log_meridian",
            "log_guiding", "log_camtemp", "log_cooler", "log_camstate"
        ))
        need_sequence = is_checked(params, "log_target")
        need_history = is_checked(params, "log_hfr") or is_checked(params, "log_stars")
        need_af = is_checked(params, "log_afresult")

        equip = get_nina_json(server, "/v2/api/equipment/info", timeout) if need_equip else None
        seq = get_nina_json(server, "/v2/api/sequence/state", timeout) if need_sequence else None
        history = get_nina_json(server, "/v2/api/image-history", timeout) if need_history else None
        last_af = get_nina_json(server, "/v2/api/equipment/focuser/last-af", timeout) if need_af else None

        nina_offline = (need_equip and equip is None) and (not need_sequence or seq is None)

        extra = {}

        if nina_offline:
            extra["AS_NINASTATUS"] = "N.I.N.A Offline"
            s.saveExtraData(extrafile, extra)
            s.log(4, "INFO: allsky_ninaequipment: N.I.N.A API unreachable")
            return "N.I.N.A Offline"

        if equip:
            mount = equip.get("Mount", {})
            fw = equip.get("FilterWheel", {})
            cam = equip.get("Camera", {})
            guider = equip.get("Guider", {})

            if is_checked(params, "log_filter"):
                extra["AS_NINAFILTER"] = (
                    fw.get("SelectedFilter", {}).get("Name", "N/A")
                    if fw.get("Connected") else "N/C"
                )

            if is_checked(params, "log_tracking"):
                tracking_on = mount.get("TrackingEnabled", False)
                extra["AS_NINATRACKING"] = mount.get("TrackingMode", "N/A") if tracking_on else "Stopped"

            if is_checked(params, "log_pier"):
                pier = mount.get("SideOfPier", "")
                extra["AS_NINAPIER"] = "E" if pier == "pierEast" else ("W" if pier == "pierWest" else "N/A")

            if is_checked(params, "log_meridian"):
                flip_h = mount.get("TimeToMeridianFlip")
                extra["AS_NINAFLIP"] = format_meridian(flip_h) if flip_h is not None else "N/A"

            if is_checked(params, "log_guiding"):
                if guider.get("Connected"):
                    state = guider.get("State", "N/A")
                    rms = guider.get("RMSError", {}).get("Total", {}).get("Arcseconds", 0)
                    extra["AS_NINAGUIDE"] = f"Guiding {rms:.2f}\"" if (state == "Guiding" and rms) else state
                else:
                    extra["AS_NINAGUIDE"] = "N/C"

            if is_checked(params, "log_camtemp"):
                temp = cam.get("Temperature")
                extra["AS_NINACAMTEMP"] = f"{temp:.1f}C" if temp is not None else "N/A"

            if is_checked(params, "log_cooler"):
                if cam.get("CoolerOn"):
                    pwr = cam.get("CoolerPower")
                    extra["AS_NINACOOLER"] = f"{pwr:.0f}%" if pwr is not None else "N/A"
                else:
                    extra["AS_NINACOOLER"] = "Off"

            if is_checked(params, "log_camstate"):
                extra["AS_NINACAMSTATE"] = cam.get("CameraState", "N/A")

        if is_checked(params, "log_target"):
            target = find_running_target(seq) if seq else None
            extra["AS_NINATARGET"] = target if target else "N/A"

        if history and isinstance(history, list) and len(history) > 0:
            last = history[-1]
            if is_checked(params, "log_hfr"):
                hfr = last.get("HFR")
                extra["AS_NINAHFR"] = f"{hfr:.2f}" if hfr is not None else "N/A"
            if is_checked(params, "log_stars"):
                stars = last.get("Stars")
                extra["AS_NINASTARS"] = str(stars) if stars is not None else "N/A"

        if last_af and isinstance(last_af, dict):
            if is_checked(params, "log_afresult"):
                pos = last_af.get("CalculatedFocusPoint", {}).get("Position")
                hfr = last_af.get("CalculatedFocusPoint", {}).get("Value")
                filt = last_af.get("Filter", "")
                extra["AS_NINAAFPOS"] = str(pos) if pos is not None else "N/A"
                extra["AS_NINAAFHFR"] = f"{filt} {hfr:.2f}" if hfr is not None else "N/A"

        s.saveExtraData(extrafile, extra)
        s.log(4, f"INFO: allsky_ninaequipment: exported {list(extra.keys())}")
        return "OK"

    except Exception as e:
        s.log(0, f"ERROR: allsky_ninaequipment: {str(e)}")
        return f"Error: {str(e)}"