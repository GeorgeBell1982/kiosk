# Desktop and Service Integration

Use desktop autostart for Raspberry Pi graphical sessions:

```bash
bash install/setup_autostart.sh
```

The generated entry uses the actual checkout path and the runtime launcher,
honors `XDG_CONFIG_HOME`, and handles spaces and special characters in paths.
It does not enable other autostart methods. Configure one startup method.

## Optional systemd user service

`kiosk-browser-user.service` is a template. Change `office_kiosk` in its paths if
needed, then install it under the application's recognized service name:

```bash
mkdir -p ~/.config/systemd/user
cp systemd/kiosk-browser-user.service ~/.config/systemd/user/office-kiosk-browser.service
systemctl --user daemon-reload
# Run from the active desktop; import whichever session variables are set.
systemctl --user import-environment DISPLAY WAYLAND_DISPLAY XDG_RUNTIME_DIR XDG_SESSION_TYPE
systemctl --user enable --now office-kiosk-browser.service
```

Disable the desktop entry before choosing the service. The desktop must activate
`graphical-session.target`; not all Raspberry Pi desktop environments do so.
The service inherits the real desktop environment and stops with the graphical
session. It does not assume a user ID or fabricate display variables.
`Restart=on-failure` avoids repeatedly relaunching after a normal or duplicate exit.

## System-wide template

`kiosk-browser.service` is an example for a separately configured dedicated kiosk.
Customize `User`, `Group`, working directory, launcher path, runtime directory,
and display variables to match the actual desktop login. Its example `pi` user,
UID 1000, and `wayland-0` are not auto-detected. The browser must run as the desktop
user, not root. Desktop-login autostart is preferable when session details vary.

Do not copy or enable this template unchanged on a differently configured host.
Install it only after dependencies and the graphical session have been validated.

## Application-menu template

`Office Kiosk Browser.desktop` is also an example with `/home/pi/office_kiosk`
paths. Customize those paths before copying it to
`~/.local/share/applications/`. It uses the launcher, so virtual-environment
selection and exit reporting stay consistent with desktop startup.
