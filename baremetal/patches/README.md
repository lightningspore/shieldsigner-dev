# Host tool patches

`rkdeveloptool-ram-location.patch` is a modification of Rockchip's GPL-2.0
rkdeveloptool source (upstream commit 304f073752fd25c854e1bcf05d8e7f925b1f4e14).
The patch remains GPL-2.0; it is not linked into the MIT firmware. Retain the
upstream license in the ignored `.tools/rkdeveloptool` checkout.

It adds `RKDEVELOPTOOL_RAM_LOCATION` (hex USB LocationID) for `db` only and
requires the selected device to be 2207:110c maskrom. Other commands are rejected
when that variable is set. `ld` still lists every target. It never enables
location-selected storage commands. The harness uses devices.json's original
DUT location 201, while DUT1 at 101 stays untouched.

Apply with `git apply /absolute/path/to/rkdeveloptool-ram-location.patch` in the
pinned checkout, then rebuild with its existing configured Makefile (`make -j4`).
The harness fails closed if the configured location is absent. Never select the
first enumerated device when multiple targets are connected.
