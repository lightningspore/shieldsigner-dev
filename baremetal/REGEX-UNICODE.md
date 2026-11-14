# Original app regex and Unicode support

Native app builds now enable MicroPython's real Unicode strings and UTF8
validation. The CORE_FEATURES default previously counted UTF8 bytes as characters
and accepted invalid UTF8; that cannot preserve original QR text/passphrase logic.
The change is limited to native app builds, which already supply libm/newlib.

The frozen `re` adapter exposes `search`, `match`, `fullmatch`, numeric match
`group`/`groups`/`start`/`end`/`span`, and I/M/S/U/X/A flags. It uses the pinned
PCRE2-10.46 C engine, including Unicode properties, without JIT or OS threads.
PCRE2 commit: b2bd4254b379b9d7dc9a3dda060a7e27009ccdff.
Upstream: https://github.com/PCRE2Project/pcre2
License: BSD-3-Clause WITH PCRE2-exception; original LICENCE.md/copyrights stay
in `.tools/pcre2` and are copied into the ignored build output. Build metadata:
`build/regex/manifest.json`.

The disposable source copy changes two `read_repeat_counts` local types from
`int32_t` to `int`. Newlib uses32-bit long for int32_t; the upstream helper takes
int pointers, so unmodified10.46 fails GCC14's incompatible-pointer check on ARM.
Both target types are32bits, and the helper now receives its declared type.
Cached upstream source stays clean. No regex algorithm was replaced.

This is a reviewed API for the app patterns, not all of CPython's re API.
Named-group lookup, compile/findall/split/sub and other APIs are not implemented;
PCRE2 syntax also differs outside the qualified patterns. Unsupported flags fail
explicitly. Limits:8192pattern bytes,1MiB subject bytes,63capture groups,
100000match operations,256depth and512KiB native match heap. Limit/error/no-match
paths free PCRE2 state before Python allocation or exceptions. Unicode match
positions count codepoints, while bytes positions count bytes.

`mise run baremetal:regex:prepare` generates expected results using CPython re.
`baremetal:regex:gate` verifies the real DUT against those results for original
animated-frame headers, QR numeric lengths, time/address headers, optional groups,
case-insensitive matching, Unicode groups/positions and byte patterns.
It also checks UTF8 rejection, malformed patterns, flags/capture/type bounds and
native heap cleanup. These are runtime prerequisites: original DecodeQR and
ScanView integration remain unfinished. The exact cold-power benchmark remains
deferred by the user; these checks do not establish full app boot or readiness.
