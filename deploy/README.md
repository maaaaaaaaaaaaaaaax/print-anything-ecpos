# deploy

Planned files for the Raspberry Pi 5:

- `printbot.service`: systemd unit, `Restart=always`, `EnvironmentFile` for secrets, `MemoryMax` as a backstop
- `99-printer.rules`: udev rule giving the service user access to the printer, `04b8:0202` for the TM-T88IV
- `install.md`: OS packages (tesseract with eng and deu, poppler-utils, LibreOffice, libmagic1) and the update flow
