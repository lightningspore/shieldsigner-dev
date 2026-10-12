# Explicit public-content allowlist. Never crawl the repo or Telegram caches.
GUIDES = [
("build-overview", "docs/BUILD-OVERVIEW.md", "Build", "Whole-device build overview", "Module, camera, case and firmware choices beyond the carrier PCB."),
("overview", "README.md", "Start here", "Project overview", "The Luckfox carrier, current progress and project sources."),
("hardware", "docs/HARDWARE.md", "Hardware", "Hardware architecture", "Power, processor, screen, buttons and the card reader."),
("components", "docs/COMPONENTS.md", "Hardware", "Every component explained", "What each of the 53 parts does, why it was chosen and how it connects."),
("kicad", "KICAD.md", "Hardware", "KiCad board & tools", "Native design, electrical checks and guarded editing tools."),
("electrical-review", "docs/ELECTRICAL-REVIEW.md", "Hardware", "Electrical review", "Supply limits, reset timing, signal paths and pending measurements."),
("smartcards", "docs/SMARTCARDS.md", "Smartcards", "Cards & the Linux reader", "Socket wiring, SeedKeeper versus Satochip, and PC/SC over UART."),
("bom", "docs/BOM.md", "Build", "Parts & JLCPCB assembly", "Carrier population, supplier matches and unresolved LCD qualification."),
("bom-table", "docs/BOM-TABLE.md", "Build", "Component catalog", "Reviewed part identities, quantities and supplier links."),
("bringup", "docs/BRINGUP.md", "Build", "Bring-up guide", "A staged path from unpowered inspection to camera and card testing."),
("bringup-results", "docs/BRINGUP-RESULTS.md", "Build", "Hardware test record", "The evidence collected so far and the tests still to run."),
("os-build", "docs/OS-BUILD.md", "Software", "Buildroot & firmware", "Pinned inputs, successful builds, caches and possible Linux-free work."),
("tscircuit", "docs/PORT-STATUS.md", "Software", "The tscircuit experiment", "What the port preserves and where its checks stop."),
("pdf-references", "docs/PDF-REFERENCES.md", "Sources", "Datasheets & references", "Locally saved supplier drawings and manufacturer documents."),
]
