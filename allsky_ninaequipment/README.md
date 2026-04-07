# allsky_ninaequipment

An [AllSky](https://github.com/AllskyTeam/allsky) module that captures live N.I.N.A imaging session for further use on your AllSky overlay — including current target, active filter, guiding RMS, camera temperature, time to meridian flip, and more.

Data is pulled from the [N.I.N.A Advanced API plugin](https://github.com/christian-photo/ninaAPI) over your local network.

---

## Requirements

- AllSky v2024.x.x or later
- [N.I.N.A](https://nighttime-imaging.eu/) v3.x with the **Advanced API plugin** (v2.2.x) installed and enabled
- N.I.N.A and AllSky must be on the same local network
- The Advanced API plugin must be bound to a LAN IP address (not localhost)

---

## N.I.N.A Advanced API Setup

1. In N.I.N.A, go to **Plugins** and install **Advanced API** if not already installed
2. After installation, go to **Options → Plugins → Advanced API**
3. Confirm **API Enabled** is ON
4. Note the **IP Address** shown — e.g. `http://192.168.1.28:1888`
5. Confirm you can reach the API from another device on your network via your command-line or terminal:

```bash
curl "http://<nina-ip>:1888/v2/api/version"
```

A successful response looks like:
```json
{"Response":"2.2.15.0","Error":"","StatusCode":200,"Success":true,"Type":"API"}
```

If the request times out, the Advanced API may be bound to localhost only. Check the IP address shown in the plugin settings — it should show your machine's LAN IP, not `127.0.0.1`.

---

## Installation

1. Install via the AllSky Module Installer for best results.
2. In the AllSky web UI, go to **Module Manager**
3. Find **NINA Equipment** in the available modules list
4. Add it to your **Night** pipeline (and optionally **Day** if you want daytime session monitoring)
5. Configure the module settings (see below)
6. Save and wait for the next image cycle

---

## Module Settings

| Setting | Default | Description |
|---|---|---|
| N.I.N.A Advanced API Server URL | `http://192.168.1.28:1888` | Full URL to your N.I.N.A Advanced API |
| Request Timeout (seconds) | `2` | How long to wait for API responses before giving up |
| Log Target Name | ✅ | Export `AS_NINATARGET` |
| Log Current Filter | ✅ | Export `AS_NINAFILTER` |
| Log Tracking Mode | ✅ | Export `AS_NINATRACKING` |
| Log Pier Side | ✅ | Export `AS_NINAPIER` |
| Log Time to Meridian Flip | ✅ | Export `AS_NINAFLIP` |
| Log Guiding State and RMS | ✅ | Export `AS_NINAGUIDE` |
| Log Camera Temperature | ✅ | Export `AS_NINACAMTEMP` |
| Log Cooler Power | ✅ | Export `AS_NINACOOLER` |
| Log Camera State | ☐ | Export `AS_NINACAMSTATE` |
| Log Last Frame HFR | ✅ | Export `AS_NINAHFR` |
| Log Last Frame Star Count | ☐ | Export `AS_NINASTARS` |
| Log Last Autofocus Result | ☐ | Export `AS_NINAAFPOS` and `AS_NINAAFHFR` |
| Extra Data Filename | `ninaequipment.json` | JSON file written to the AllSky extra data directory |

Only checked items are fetched and exported. Unchecked items generate no API calls and no overlay variables, keeping your overlay variable list clean.

---

## Exported Overlay Variables

These variables become available in the AllSky Overlay Manager once the module runs successfully.

| Variable | Example | Description |
|---|---|---|
| `AS_NINATARGET` | `NGC 7822` | Current sequence target name |
| `AS_NINAFILTER` | `Ha` | Active filter wheel position |
| `AS_NINATRACKING` | `Sidereal` | Mount tracking mode, or `Stopped` |
| `AS_NINAPIER` | `E` | Pier side — `E` (East) or `W` (West) |
| `AS_NINAFLIP` | `02:44` | Time to next meridian flip (HH:MM) |
| `AS_NINAGUIDE` | `Guiding 0.45"` | PHD2 state and total RMS error, or `Stopped` / `N/C` |
| `AS_NINACAMTEMP` | `-10.0C` | Camera sensor temperature |
| `AS_NINACOOLER` | `41%` | Cooler power percentage, or `Off` |
| `AS_NINACAMSTATE` | `Exposing` | Camera state (`Idle`, `Exposing`, `Downloading`, etc.) |
| `AS_NINAHFR` | `1.62` | HFR value from the most recent captured frame |
| `AS_NINASTARS` | `428` | Star count from the most recent captured frame |
| `AS_NINAAFPOS` | `4290` | Focuser position from last autofocus run |
| `AS_NINAAFHFR` | `Ha 0.75` | Filter and HFR achieved at last autofocus |
| `AS_NINASTATUS` | `N.I.N.A Offline` | Only present when the API cannot be reached |

---

## Overlay Configuration Examples

In the AllSky Overlay Manager, enable new variables in the variable manager, then add text fields and reference the exported variables using `${VARIABLE_NAME}` syntax. Below are a few examples - customize to your pleasure.

**Basic imaging status line:**
```
${AS_NINATARGET} | ${AS_NINAFILTER} | Guide: ${AS_NINAGUIDE}
```
Example output: `NGC 7822 | Ha | Guide: Guiding 0.45"`

**Camera and thermal line:**
```
Cam: ${AS_NINACAMTEMP} | Cooler: ${AS_NINACOOLER} | HFR: ${AS_NINAHFR}
```
Example output: `Cam: -10.0C | Cooler: 41% | HFR: 1.62`

**Mount status line:**
```
Tracking: ${AS_NINATRACKING} | Pier: ${AS_NINAPIER} | Flip: ${AS_NINAFLIP}
```
Example output: `Tracking: Sidereal | Pier: E | Flip: 02:44`

**Minimal single-line summary:**
```
${AS_NINATARGET} [${AS_NINAFILTER}] RMS:${AS_NINAGUIDE}
```
Example output: `NGC 7822 [Ha] RMS:Guiding 0.45"`

---

## Behavior Notes

**When N.I.N.A is offline or unreachable:**
The module exports a single `AS_NINASTATUS` variable set to `N.I.N.A Offline` rather than populating all fields with `N/A`. You can add this variable to your overlay as an optional status indicator.

**When no sequence is running:**
`AS_NINATARGET` returns `N/A`. All equipment fields (filter, temperature, etc.) still reflect the current connected hardware state.

**Target name detection:**
The module identifies the active target by walking the sequence tree and finding the currently `RUNNING` target container. It uses the target name as defined in N.I.N.A's sequencer — this is the name you gave your target when setting up the sequence, not the filename.

**Image history (HFR/Stars):**
`AS_NINAHFR` and `AS_NINASTARS` reflect the most recently completed frame, regardless of whether the sequence is actively running. Values persist from the last captured frame until a new one is taken.

**Autofocus result:**
`AS_NINAAFPOS` and `AS_NINAAFHFR` persist from the last autofocus run and do not clear between sessions until N.I.N.A is restarted.

---

## Troubleshooting

**Module not appearing in Module Manager:**
Confirm instalation by re-running the Module Installer tool - `allsky_ninaequipment` should be checked, if not - check and continue. If it's checked and not working, un-check and continue, then re-run the installer and attempt again. If issues remain, check GitHub for methods to submit a help request.

**Module appears but does not run:**
Check the `Debug Info` (bug icon) in the Module Manager for errors. 

Check the AllSky log for import errors:
```bash
grep -i nina /var/log/allsky.log
```

**All values showing N/A or AS_NINASTATUS showing Offline:**
- Confirm the Advanced API plugin is enabled in N.I.N.A
- Test the API from the AllSky Pi directly:
```bash
curl "http://<nina-ip>:1888/v2/api/version"
```
- Check that the IP in the module settings matches the IP shown in N.I.N.A's Advanced API plugin options
- Confirm no firewall is blocking port 1888 on the N.I.N.A machine

**AS_NINATARGET always shows N/A:**
The target name is only populated when a sequence is actively running and a target container has `RUNNING` status. It will show `N/A` when the sequence is idle, paused, or finished.

---

## API Endpoints Used

This module uses the following N.I.N.A Advanced API v2 endpoints:

| Endpoint | Used for |
|---|---|
| `/v2/api/equipment/info` | Filter, mount, camera, guider state |
| `/v2/api/sequence/state` | Active target name detection |
| `/v2/api/image-history` | Last frame HFR and star count |
| `/v2/api/equipment/focuser/last-af` | Last autofocus result |

---

## Version History

| Version | Notes |
|---|---|
| v0.2.0 | Checkbox controls per field, offline detection, improved target name via `Target.TargetName`, image history and autofocus endpoints added |
| v0.1.0 | Initial release |

---

## Credits

- [N.I.N.A Advanced API](https://github.com/christian-photo/ninaAPI) by Christian Palm
- [AllSky](https://github.com/AllskyTeam/allsky) by the AllSky Team
- [Author](https://github.com/jcauthen78) Long-term AllSky abuser 🤓
