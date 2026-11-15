# Original settings menus on the native UI

`tools/prepare_settings_views.py` verifies the locked original SeedSigner source,
then generates all 18 original settings View classes with method coverage recorded
in `app/settings-views-provenance.json`. Five are enabled: the settings menu,
backup-load menu, locale menu, setting selection, and selection-required warning.
Original destinations, option ordering, single/multiselect updates, mandatory
selection checks, return selection, and scroll restoration are retained.

The only View-body adaptation reads the real native menu scroll snapshot instead
of a PIL button object's scroll attribute. `settings_screens.py` uses the actual
native list screen and original Linux adapter selection/help presentation.
The typed `ui.scroll_y()` / `ui.scroll_to_y()` APIs use the same tallest direct
scrollable body selection as the existing Linux native host. No widget metadata
or OS service is fabricated.

Unsupported OS/hardware utilities and numeric-keyboard PBKDF2 entry fail explicitly
before execution. NativeSettingsPlatform continues to reject unsupported driver,
locale, and persistent-storage changes before mutation. Existing supported settings
remain RAM-only. Backup menu choices retain their original destinations; those
providers require separate ports and are not claimed operational here.

Root integration: freeze `seedsigner_port/view_settings.py` and
`seedsigner_port/settings_screens.py`; map `seedsigner.views.settings_views` to
`seedsigner_port.view_settings` in the dependency resolver. The generated views
bind their own settings screen module directly. Retain the native scroll APIs.

Regenerate and validate on the host:

```sh
uv run --python 3.13 python baremetal/tools/prepare_settings_views.py
uv run --python 3.13 python -m unittest discover -s baremetal/tests -p test_settings_views.py -v
```

Host tests compare the original View decisions directly, including empty
multiselect/back, and check real-session scroll capture/restore boundaries.
Device presentation, scroll placement, and button navigation still require a
scheduled hardware gate. No device access was performed for this port.
