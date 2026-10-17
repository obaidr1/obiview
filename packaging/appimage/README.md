# AppImage package

The AppImage is built from Ubuntu 24.04 runtime packages with appimage-builder. It includes the Python/GTK runtime, Pillow, application code, and design tokens. Device drivers and hardware-specific integrations remain provided by the host system.

Build on an Ubuntu 24.04 x86-64 machine with `python3-venv`, `python3-pip`, and `libfuse2t64` available:

```bash
python3 -m venv .venv-appimage
. .venv-appimage/bin/activate
python -m pip install appimage-builder
appimage-builder --recipe packaging/appimage/AppImageBuilder.yml --skip-test
```

The output is `Bildblick-0.11.2-x86_64.AppImage`. AppImages need the FUSE 2 compatibility library on systems where it is not installed. Before describing a build as generally compatible, test it on supported distributions and desktops.
