This repository is a compact control stack for rapidly **re-configuring an optical circuit-switched network**.  The Python side drives a Qontrol power supply to retune on-chip microrings, broadcasts start/finish markers to hosts with raw ICMP, and ships example network scripts.  The key pieces are `switch_ctrl.py`, a thin wrapper around the vendor driver ([raw.githubusercontent.com](https://raw.githubusercontent.com/Flasew/reconfig_controller/main/switch_ctrl.py), [raw.githubusercontent.com](https://raw.githubusercontent.com/Flasew/reconfig_controller/main/Qontrol.py)); `icmp_ctrl.py`, which hand-crafts the ICMP headers ([raw.githubusercontent.com](https://raw.githubusercontent.com/Flasew/reconfig_controller/main/icmp_ctrl.py)); the declarative topology in `switch_config.py` ([raw.githubusercontent.com](https://raw.githubusercontent.com/Flasew/reconfig_controller/main/switch_config.py)); and the orchestration loop in `run.py` ([raw.githubusercontent.com](https://raw.githubusercontent.com/Flasew/reconfig_controller/main/run.py)).  A demo shell script applies a custom `reconfig` qdisc to each host NIC ([raw.githubusercontent.com](https://raw.githubusercontent.com/Flasew/reconfig_controller/main/set_demo.sh)), so **you’ll need the kernel in this repo built and loaded first**.  


# reconfig_controller

> End-to-end control software for **dynamic optical network reconfiguration**.

This project orchestrates both the **switch** (via Qontrol electronics) and the **hosts** (via custom ICMP control frames) so that traffic can be safely drained, paths retuned, and service resumed in a few milliseconds.

---

## Repository layout

| Path | Role |
|------|------|
| `Qontrol.py` | Vendor Python API for the Qontrol **QX** family power supplies (included verbatim). |
| `switch_ctrl.py` | Wrapper that sets per-ring voltages using `Qontrol.QXOutput`. |
| `switch_config.py` | Declarative list of `SwitchConfiguration` objects and the host table—edit this to describe *your* topology. |
| `icmp_ctrl.py` | Crafts raw IPv4/ICMP packets (`type = 9`) to signal **config-start** and **config-finish** to each host. |
| `run.py` | Reference loop that alternates between the example configurations, coordinating the two controllers. |
| `run.ipynb` | Jupyter notebook version of the same flow for quick experimentation. |
| `set_demo.sh` | Helper that attaches the custom `reconfig` qdisc, sets demo IPs/ARP entries, and bumps MTU to 9 kB. |
| `linux-reconfig/` | Out-of-tree implementation of the **reconfig** qdisc. Build & load this **before** running any host-side script. |
| misc | `__init__.py`, `.gitignore`, etc. |

---

## Quick demo

```bash
git clone https://github.com/Flasew/reconfig_controller.git
cd reconfig_controller

# make && insmod kernel/reconfig.ko   # build+load the qdisc (see kernel/README)
python run.py                         # cycles between SWITCH_CONFIG_1 and 2
````

`run.py` will

1. zero the switch,
2. send *config-start* ICMP markers,
3. apply the voltages,
4. wait for guard times,
5. send *config-finish* markers, and
6. sleep for the per-config `duration` before repeating.

---

## Requirements

* Python 3.9+ with `pyserial`, `numpy`, `pyvisa`
* Access to a **Qontrol QX** device on `/dev/ttyUSB?`
* The **reconfig** kernel module built & loaded on every host NIC that carries circuit traffic

---


