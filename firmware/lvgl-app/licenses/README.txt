ShieldSigner isolated LVGL payload notice inventory

These files retain verified third-party notices. They do not establish a license
for upstream code/assets that lack a grant. The payload remains a development
artifact with licenseClosureVerified=false.

Sources:
- SeedSigner-MIT.txt: original application MIT notice (pinned source).
- nlohmann-json-MIT.txt: https://github.com/nlohmann/json/blob/v3.11.3/LICENSE.MIT
  The bundled 3.11.3 header's SPDX copyright (2013-2023 Niels Lohmann) is separately
  retained in notice-audit.json; the upstream license file says 2013-2022.
- Apache-2.0.txt: https://www.apache.org/licenses/LICENSE-2.0.txt
- Montserrat-OFL.txt and FontAwesome5-LICENSE.txt: exact pinned LVGL built-in font
  notices. The complete OFL terms are also the version referenced by the Noto,
  Inconsolata and newer Open Sans metadata; each family's own copyright remains
  in font-name-records.json. Montserrat's copyright is not assigned to those fonts.
- Zig-MIT.txt, musl-COPYRIGHT.txt, libcxx-LICENSE.txt, libcxxabi-LICENSE.txt and
  libunwind-LICENSE.txt: Zig 0.15.2 distribution used for the static ARM build.
- font-name-records.json: extracted name IDs 0,1,2,3,5,6,13,14 and SHA256 from the
  pinned application/screens/language-pack font files. Includes the original
  application's full font directory for context; this is not a claim that every
  listed face is embedded in the native host. Reproduce with audit_licenses.py in
  the digest-pinned font-builder container.

Open items:
- The pinned seedsigner-lvgl-screens tree has no top-level license grant; GitHub's
  repository license endpoint also returned 404 during this audit.
- seedsigner-icons.otf has no embedded copyright or license name records. Its
  applicable provenance/terms, including any constituent glyphs, remain open.
- Existing application, Python packages, Rust camera runtime and OS notices are
  separate image-level dependencies; these additions do not audit all of them.

No license grant is inferred merely from a public repository or a parent project.
