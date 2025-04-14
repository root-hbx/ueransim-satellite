<p align="center">
  <a href="https://github.com/aligungr/UERANSIM"><img src="/.github/logo.png" width="75" title="UERANSIM"></a>
</p>
<p align="center">
<img src="https://img.shields.io/badge/UERANSIM-v3.2.7-blue" />
<img src="https://img.shields.io/badge/3GPP-R15-orange" />
<img src="https://img.shields.io/badge/License-GPL--3.0-green"/>
</p>

This repo is inspired by [UERANSIM](https://github.com/aligungr/UERANSIM/wiki).

## Branch

- `master`: stable, the same as original UERANSIM repo
- `free5gc`: UERANSIM && free5gc, currently maintain the same as original UERANSIM repo
- `open5gs`: UERANSIM && open5gs, interacting with [opensat: tcp-gen](https://github.com/root-hbx/open5gs-satellite/tree/tcpgen)
- `mm-switch`: UERANSIM && (open5gs1 -> open5gs2)
    - interacting with [opensat: mm-switch](https://github.com/root-hbx/open5gs-satellite/tree/mm-switch)
    - for [#issue 5](https://github.com/root-hbx/open5gs-satellite/issues/5)
- `udp-test`: UERANSIM && (open5gs1 -> open5gs2)
    - iPerf client scripts
    - interacting with [opensat: tcpgen (open5gs1)](https://github.com/root-hbx/open5gs-satellite/tree/tcpgen) and [opensat: mm-switch (open5gs2)](https://github.com/root-hbx/open5gs-satellite/tree/mm-switch)
    - `ueransim/scenario/main.py`
    - for [#issue 6](https://github.com/root-hbx/open5gs-satellite/issues/6)
- `tcp-test`: UERANSIM && (open5gs1 -> open5gs2)
    - iPerf client scripts
    - interacting with [opensat: tcpgen (open5gs1)](https://github.com/root-hbx/open5gs-satellite/tree/tcpgen) and [opensat: mm-switch (open5gs2)](https://github.com/root-hbx/open5gs-satellite/tree/mm-switch)
    - `ueransim/scenario/main.py` and `ueransim/scenario/stable_flow.py`
    - for [#issue 7](https://github.com/root-hbx/open5gs-satellite/issues/7)
- `iperf-server`: UERANSIM && (open5gs1 -> open5gs2)
    - iPerf server scripts, directly running on iPerf Server Machine
    - `ueransim/scenario/server_monitor.py`

