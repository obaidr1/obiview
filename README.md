<p align="center">
  <img src="assets/local.bildblick.Viewer.svg" width="160" alt="Bildblick kingfisher logo in blue and orange">
</p>

# Bildblick

**Browse images, make quick edits, and export exactly what you need — on your Linux desktop.**

Bildblick is a local GTK 4 desktop image viewer and editor. Browse image folders, crop or resize pictures, adjust color, and save with format-specific options. It also includes batch processing, named export profiles, and a command-line interface.

The interface follows the system language and is available in English and German. Set `BILDBLICK_LANGUAGE=en` or `BILDBLICK_LANGUAGE=de` to choose a language at launch. Image editing does not require an account or cloud service.

**Version 0.11.2 · early release · MIT license · reference system: Fedora 44**

## Contents

- [Features](#features)
- [Installation](#installation)
- [Getting started](#getting-started)
- [Keyboard shortcuts](#keyboard-shortcuts)
- [Resizing](#resizing)
- [Saving and export profiles](#saving-and-export-profiles)
- [Batch processing and CLI](#batch-processing-and-cli)
- [Formats and multipage files](#formats-and-multipage-files)
- [Data storage and limitations](#data-storage-and-limitations)
- [Development and tests](#development-and-tests)
- [Report issues and contribute](#report-issues-and-contribute)

The [product document](PRODUCT.md) describes the intended audience, interaction model, product scope, and next development steps.

## Features

| Area | Available features |
| --- | --- |
| Viewing | Zoom, fit to window, 100% view, fullscreen, transparency checkerboard |
| Navigation | Open folders, natural filename sorting, thumbnails, filename filter |
| Editing | Fine rotation, flip, precise selections, crop, pixels/percent/cm/inches/DPI, undo and redo |
| Color and detail | Gamma, RGB balance, brightness, contrast, saturation, red-eye correction, histogram, color channels, palette, ten effects |
| Additions | Text in a selection, drawing, borders, canvas extension, image watermark, panorama layout |
| Export | Format selection, JPEG/GIF/PNG/WebP options, metadata controls, profiles |
| Batch | Batch conversion, resized output, renamed copies, preview, cancellation |
| Multipage | Page/frame navigation, animation, export to TIFF, GIF, WebP, or PDF |
| Desktop | Application menu, clipboard, multiple windows, file actions, custom print size and position |
| Optional system features | Scanning through SANE; audio/video through GTK and GStreamer |
| Automation | CLI with JSON results, preview mode, and error status |

Print layout is implemented, but printing to a physical printer has not yet been confirmed. Key graphical workflows are also checked in a GTK session in GitHub Actions. See [Development and tests](#development-and-tests) for the current test status.

## Installation

### Requirements

Bildblick needs a graphical Linux session and these system libraries:

| Component | Purpose |
| --- | --- |
| `/usr/bin/python3` | Runs the app and installer |
| GTK 4 and PyGObject | Native windows and dialogs |
| Pycairo | Image canvas and printing |
| Pillow 12 or later | Image operations and standard codecs |
| GdkPixbuf | Displays image data and icons |
| Fontconfig (`fc-match`) and installed fonts | Font families and styles for inserted text |

The reference system uses Python 3.14, GTK 4.22, and Pillow 12.3. Other distributions may work, but have not all been verified as complete configurations.

Install the core dependencies on Fedora:

```bash
sudo dnf install python3 python3-gobject python3-cairo python3-pillow gtk4 fontconfig
```

Optional decoders provide additional formats:

```bash
sudo dnf install ImageMagick poppler-utils ffmpeg-free util-linux
```

Scanning also requires `sane-backends` and a configured scanner. Media playback needs the GTK media backend and suitable GStreamer codecs. Both are optional; the app reports when support is unavailable.

Available formats and extra decoders depend on the codecs installed on the system. The installer does not download dependencies or install system packages.

### Install a packaged version

#### Flatpak (recommended for Ubuntu and other distributions)

The Flatpak bundles the image-processing dependency and uses a shared GTK runtime, so you do not need to install Python, GTK, and Pillow through your distribution's package manager.

1. Install Flatpak and enable Flathub (on Ubuntu, use the Software app or the [Flatpak setup guide](https://flatpak.org/setup/)).
2. Download `Bildblick-0.11.2.flatpak` from [GitHub Releases](https://github.com/obaidr1/obiview/releases).
3. Open the file with your software installer, or run this from the download directory:

```bash
flatpak install --user ./Bildblick-0.11.2.flatpak
```

Bildblick will then appear in your application menu. The file chooser grants access to images and folders you open. The first Flatpak release targets x86-64 PCs; other architectures are not included yet.

#### AppImage (portable download)

Download `Bildblick-0.11.2-x86_64.AppImage` from [GitHub Releases](https://github.com/obaidr1/obiview/releases), make it executable, and launch it:

```bash
chmod +x Bildblick-0.11.2-x86_64.AppImage
./Bildblick-0.11.2-x86_64.AppImage
```

The AppImage includes an Ubuntu 22.04 based GTK/Python runtime. Some systems may need the FUSE 2 compatibility library. The x86-64 Flatpak remains available for users who prefer software-center installation and sandboxed file access.

#### Manual system install

1. Download `Bildblick-0.11.2-linux.tar.gz` from [GitHub Releases](https://github.com/obaidr1/obiview/releases).
2. Extract the archive.
3. Run `install.sh` from the extracted directory.
4. Search for **Bildblick** in your application menu.

```bash
tar -xzf Bildblick-0.11.2-linux.tar.gz
cd Bildblick-0.11.2
./install.sh
```

This installs into your user account and does not require `sudo`. It leaves your current default image viewer unchanged and adds Bildblick as an **Open With** option. This variant still needs the system dependencies listed above.

The archive contains the application code, documentation, and icon. The system provides the Python/GTK runtime; this package is not a standalone AppImage.

### Run or install from source

From the project directory:

```bash
./start.sh
./start.sh /path/to/image.jpg
./start.sh /path/to/image-folder
```

To add a persistent application menu entry:

```bash
/usr/bin/python3 packaging/install.py --source .
```

After updating, close any running instance and reopen Bildblick from the application menu. Changes in the source directory appear in the installed copy after reinstalling it.

### Install locations

| Content | Default location |
| --- | --- |
| Application files | `~/.local/share/bildblick/app/` |
| Terminal launcher | `~/.local/bin/bildblick` |
| Menu entry | `~/.local/share/applications/io.github.obaidr1.obiview.desktop` |
| Icon | `~/.local/share/icons/hicolor/scalable/apps/io.github.obaidr1.obiview.svg` |
| Export profiles | `~/.config/bildblick/save-profiles.json` |
| Viewing options | `~/.config/bildblick/viewer.json` |
| Last ten image folders | `~/.config/bildblick/recent.json` |

`XDG_DATA_HOME` and `XDG_CONFIG_HOME` are respected for data and configuration. The terminal launcher is placed under `~/.local/bin` regardless.

To uninstall, remove the application files, launcher, menu entry, and icon listed above. Export profiles can be kept separately. Your image files remain outside the installation.

## Interface and image adjustments

**Consistent editing dialogs:** Brightness/contrast/color, sharpen/blur, fine rotation, borders, red-eye correction, color reduction, channel swapping, auto-crop, canvas, and text use a large live preview with original comparison, reset, apply, and cancel. Strength, contrast, saturation, sharpness, angle, tolerance, and color count use sliders. Border styles, channel orders, and drawing tools are direct buttons. Changes become one undo step only after you apply them.

For border and stroke widths, a precise number field accompanies the slider. Image dimensions, DPI, positions, and filenames remain precise input fields. Units, interpolation methods, presets, selection ratios, print modes, and additional export formats are directly selectable. PNG compression and quality in export and batch options also use sliders.

New tool previews are calculated in the background from the original pixels and then scaled for display. Large images may take longer to process. Applying while a calculation is running waits for the current valid preview; cancellation remains available. Stale results are discarded. The existing effects dialog and image-adjustment panel continue to use reduced working previews.

Bildblick uses a light monochrome interface with rounded cards and dark primary actions. The main window starts at **720 × 640 pixels**. A visible menu bar and a compact toolbar sit above the image; the status bar is at the bottom. Open, save, crop, history, image information, zoom, navigation, resize, and image adjustments are directly accessible. The canvas has no floating controls or editing bar.

- **Looks:** Original, Film, Fade, and Warm.
- **Light:** RGB histogram, brightness, contrast, gamma, highlights, and shadows.
- **Color:** Temperature, saturation, vibrance, and red/green/blue balance.
- **Effects:** Grain, vignette, and sharpness.

**Image → Adjustments** or the adjustment icon opens a separate dialog with image preview, looks, and sliders. Thumbnails also open in a separate window. Sliders show a preview first. **Apply** commits it as an undoable edit; **Reset** discards the preview. Saving and other image operations apply pending adjustments before continuing. The preview is reduced for a quick response; applying processes the image at full resolution. The histogram is based on the preview and is intended as a guide.

The menu bar contains **File**, **Edit**, **Image**, **View**, **Extras**, and **Help**. Common actions have keyboard shortcuts; the table below lists the current mapping. The interface uses the light appearance; a separate dark theme is not included.

## Getting started

1. **Open an image:** press `Ctrl+O` or drop a single file onto the window.
2. **Browse a folder:** choose a folder from **File → Open Folder**. Show thumbnails and filter by filename from **View**.
3. **Adjust the view:** press `F` to fit to the desktop, `Ctrl+H` for 100%, or `+` and `−` to zoom.
4. **Edit:** drag a selection to crop, rotate the image, or press `Ctrl+R` to resize it.
5. **Save:** press `Ctrl+Shift+S` to choose a filename, destination, format, and options.

When you move to another image or close the window, Bildblick asks about unsaved changes. Changes are saved only when you explicitly choose a save action.

## Image information

Press **I** or choose **Image → Image Information** to view the filename, directory, full path, format, separate X/Y DPI, original and current dimensions with megapixels and aspect ratio, print size in cm and inches, original and current color depth, counted RGB colors, file size, current pixel-buffer memory, folder position, modification date, load time, and page/frame.

Color counting runs in the background and can be disabled. Different alpha values are not counted as extra RGB colors. Pixel memory does not include the entire process or undo history. Missing source data is marked unavailable; an original color depth is not guessed for externally rasterized formats.

**Change** updates X/Y DPI without changing pixel dimensions and can be undone. If no valid resolution exists, the assumed default of 96 DPI is identified. EXIF, IPTC, and comments have separate read-only views. This is not a full metadata editor; complete IPTC preservation on export is not guaranteed.

## Keyboard shortcuts

The [complete shortcut list](docs/SHORTCUTS.md) is searchable in the app with **F1**. While zoomed in, arrow keys scroll the image; otherwise, they change files.

| Shortcut | Action |
| --- | --- |
| `O`, `Ctrl+O` | Open image |
| `S`, `Ctrl+Shift+S` | Save as |
| `Ctrl+S` | Open save dialog |
| `Ctrl+R` | Resize |
| `I` | Image information |
| `Ctrl+Z` / `Ctrl+Shift+Z` | Undo / redo |
| `Ctrl+Y` | Crop selection |
| `Ctrl+C` / `Ctrl+V` | Copy selection or whole image / paste image as a new document |
| `Ctrl+X` / `Ctrl+A` | Cut selection / select all |
| `Shift+C` | Custom selection |
| `Shift` + arrow keys | Move selection by one pixel |
| `Ctrl+T` | Insert text into selection |
| `Ctrl+N` | Open working image in a new window |
| `D` | Clear image from screen, keep file |
| `Shift+R` | Reopen saved file |
| `Ctrl+F` | Search thumbnail filenames |
| `F2` | Rename file |
| `F12` | Draw |
| `Ctrl+P` | Print |
| `R` | Rotate 90° clockwise |
| `+` / `−` | Zoom in / out |
| `F` / `Ctrl+H` | Fit to desktop/window / 100% |
| `←` / `→` | Previous / next file in folder |
| `Ctrl+Page Up` / `Ctrl+Page Down` | Previous / next page or frame |
| `Esc` | Exit selection mode |
| `F5` / `F9` | Refresh view / start or stop slideshow |
| `Enter` | Toggle fullscreen |
| `F11` | Enter fullscreen; toggle pointer visibility there |
| `F1` | Searchable keyboard help |

## Resizing

**Image → Resize**, the visible resize button, and `Ctrl+R` open the same dialog.

- Enter width and height in **pixels**, **percent**, **centimeters**, or **inches**.
- When aspect ratio is locked, changing one dimension updates the other.
- Percentages are based on the image size when the dialog opened.
- Presets include 25%, 50%, 100%, and 200%; enter any other value directly.
- Size presets range from 640 × 480 to 3840 × 2160 and include screen size. With aspect ratio locked, the image is fitted within those dimensions.
- **DPI** sets physical print size. Changing DPI alone does not create detail and can be undone. JPEG, PNG, TIFF, BMP, and PDF preserve print resolution on export. Print resolution is retained even when private metadata is disabled.
- Interpolation options are Lanczos, bicubic, bilinear, and nearest neighbor.
- The target dimensions and megapixel count are shown before applying.

Resizing changes the edit state and can be undone. Changing zoom only changes the view.

## Selections, corrections, and additions

Drag with the left mouse button to create a rectangle. Drag its edges or corners to resize it; use the right mouse button to move it. **Edit → Custom Selection** offers position, pixel/cm/inch dimensions, DPI, and fixed aspect ratios. With a fixed ratio, width determines height. **Maximize and center selection** expands the crop to the image edge while preserving its ratio.

**Ctrl+C** copies the selection, or the whole image when there is no selection. Choose **File → New Window**, then press **Ctrl+V**, to create a separately saveable document. **Ctrl+X** copies the selection and replaces its pixels with white. **Clear Outside Selection** preserves the canvas size and fills the outside white. **Remove Solid Borders** detects transparent borders or the top-left background color; tolerance is adjustable.

**Image → Fine Rotation** uses degrees, with positive values rotating clockwise. The expanded canvas and border color are configurable. **Red-eye Correction** needs a tight selection around the eye and changes only red-dominant pixels inside it.

**Effects** includes 3D button, blur, emboss, oil paint, edge detection, median, explosion, pixelize, sepia, and raindrops. Each effect is directly selectable with its own button; there is no dropdown. A large live preview shows the changes. The strength slider blends each effect with the original; depending on the effect, additional controls adjust radius, edge width, pixel size, scatter, or droplet pairs. **Compare with Original** shows the unchanged image. Settings remain when switching between effects. **Reset Effect** resets the selected effect. **Apply** commits it at full resolution as one undoable step; **Cancel** discards the preview. For large images, the preview is reduced and pixel-dependent effects may differ from the full-resolution result. **Reduce Colors** offers 2–256 colors and dithering. **Swap Color Channels** swaps RGB channels; a separate histogram dialog shows the full image distribution.

**Add Border** offers simple, double, and raised frames with width and color controls. **Extend Canvas** sets each side separately: positive values add canvas and negative values crop it. **Join Images** arranges multiple images horizontally or vertically with spacing; it does not blend a perspective panorama.

**Insert Text** uses the selected font family, style, point size, and color. Text wraps inside the selection. Without a selection, it starts 20 pixels from the top-left. Point-to-pixel conversion uses the image DPI. **Edit → Draw** opens a separate dialog for pen, soft brush, line, arrow, rectangle, and ellipse. Each of the six tools has its own icon and text label. Strokes can be undone in the dialog; applying creates one undo step.

## Files, view, and printing

The File menu includes **Reopen**, **Open With**, **Search Files**, **Recent Folders**, **Rename**, **Copy**, **Move**, and **Move to Trash**. File actions operate on saved files; pending edits must first be saved or discarded. Copy, move, and rename do not overwrite an existing target. Deletion asks for confirmation and uses the system trash only.

Use **Extras → View Settings** to configure the background color and whether small images are enlarged when fitted. Settings are stored locally. The main window starts at 720 × 640 pixels. At manual zoom or 100%, it grows with the image up to the available screen area and maximizes at that limit. Further zoom uses scrollbars; zooming out does not automatically shrink the window.

**Print** first opens the image layout: portrait/landscape, best fit, custom size in cm with linked aspect ratio, or independent scaling in percent. Centering and offsets from the top/left printable page edge are configurable. The native print dialog then selects the printer, paper, and device options. Oversized images are clipped at the printable page edge. PDF output is checked automatically; a physical printer has not yet been verified.

**Scan** uses SANE for device, resolution, and color selection. **Scan and Print** continues to print layout after scanning. Scanners may require different modes or DPI values; driver errors are shown. The hardware workflow has not been tested with a real scanner. **Open Audio / Video** plays local media in a separate window using GTK controls when the system supports its codec; media is not edited as an image.

See [docs/FEATURES.md](docs/FEATURES.md) for a full list of visible menu actions and their limitations.

## Saving and export profiles

The save dialog provides a filename, destination folder, format selector, and relevant options. The suggested name is `<name>-edited` in the supported source format; otherwise PNG is selected. The file extension follows the chosen format.

JPG, PNG, and WebP are shown as direct-choice cards. **More Formats** contains the remaining output formats. The file-size display is calculated in the background by encoding with the selected settings; it is not a generic estimate. This can take a little while for large files.

**Resolution** offers 50%, 100%, and custom pixel dimensions with a locked aspect ratio. A reduced export does not change the editor's working image or save state. This size setting applies to the current export; named profiles may include their own output dimensions.

Change the filename and destination under **Location**. **Remove Metadata** disables EXIF, ICC, comments, and XMP together. Individual metadata options, format-specific settings, and named profiles are under **Advanced Options & Profiles**.

### Format options

| Format | Options |
| --- | --- |
| JPEG | Quality 1–100, progressive, grayscale, disable chroma subsampling (4:4:4), maximum file size |
| GIF | Interlacing, preserve transparency or flatten to white |
| PNG | Lossless compression from 0 to 9 |
| WebP | Quality and lossless mode |
| TIFF, BMP, ICO, PDF, JPEG 2000, PPM | Export using the format's available standard options |

The JPEG size limit is specified in **KiB**; 1 KiB equals 1,024 bytes. If needed, Bildblick lowers quality below the selected starting value. If the limit cannot be met even at quality 1, export fails with a clear message and an existing target file is preserved. The limit does not automatically change pixel dimensions.

PNG compression is always lossless: higher levels generally save more space and take more processing time; they do not reduce image quality. GIF has no JPEG-style quality setting.

GIF supports at most 256 colors and binary transparency only. With transparency enabled, pixels with alpha below 50% become transparent. The remaining partially transparent pixels are composited against white. The encoder uses interlacing only for images at least 16 × 16 pixels.

JPEG, BMP, PDF, and PPM use a white background for transparent images. ICO output is reduced to supported icon sizes. Export options such as JPEG grayscale do not alter the editor image.

### Metadata

EXIF, ICC color profile, original comment, and XMP can be preserved separately. Only metadata that was read and is supported by the target format can be retained.

| Data | Supported single-image output formats |
| --- | --- |
| EXIF | JPEG, PNG, WebP |
| ICC | JPEG, PNG, WebP, TIFF, PDF, where supported by the encoder |
| Comment | JPEG, GIF |
| XMP | JPEG, WebP |

EXIF orientation is normalized when loading. An original RGB color profile is not attached to a grayscale JPEG. IPTC, embedded previews, and specialized format metadata are not fully preserved. Bildblick does not include a metadata editor.

### Profiles

Enter a name in **Profiles** and save the current settings. **Load** applies an existing profile; **Delete** removes it. Saving an existing name updates that profile.

Profiles store format and save options, but not image files or destination paths. They persist after restarting the app. Options last used without a named profile apply only for the current session.

## Batch processing and CLI

Under **Extras → Batch Processing**, choose source files, destination folder, format, maximum size, and filename template. Before starting, Bildblick previews source-to-destination names. Existing targets and filename collisions are rejected.

Allowed placeholders are `{stem}`, `{index}`, and numerically formatted indices such as `{index:04d}`. Example: `Holiday-{index:04d}-{stem}`.

The `copy` mode creates renamed, byte-for-byte copies. Image conversion can also resize and rotate by 90°. Cancellation stops after the current file. Multipage sources are rejected for single-image conversion so pages are not silently lost.

### Preview without writing files

The destination folder must already exist:

```bash
/usr/bin/python3 cli.py ./images --output ./export \
  --format jpg --max-width 1920 --quality 90 \
  --pattern 'Image-{index:04d}' --dry-run
```

Without `--dry-run`, the planned job is executed. Folders are read without descending into subfolders. Multiple files and folders can be supplied as sources together.

### More examples

```bash
# Fit within a 1600 × 1200 rectangle without enlarging small images
/usr/bin/python3 cli.py photo.png --output ./export \
  --format webp --max-width 1600 --max-height 1200

# Byte-for-byte copies with sequential names
/usr/bin/python3 cli.py ./images --output ./copies \
  --format copy --pattern 'Archive-{index:04d}-{stem}'

# JPEG output without preserved metadata
/usr/bin/python3 cli.py ./images --output ./export \
  --format jpg --quality 85 --strip-metadata
```

The CLI writes JSON containing source path, destination path, and result. Exit code `0` means success, `1` means at least one processing error, and `2` means an argument or planning error. The advanced save dialog and its profiles are not fully represented by CLI options.

## Formats and multipage files

Standard formats are read through Pillow. Additional formats use native decoders already installed on the system. A recognized file extension does not guarantee every variant of a format is supported.

| Area | Status |
| --- | --- |
| PNG, JPEG, WebP, GIF, BMP, TIFF | Core read/write formats |
| ICO, JPEG 2000, PPM | Export through installed Pillow codecs |
| PDF | Read through Poppler and rasterized at 150 dpi; raster PDF output |
| SVG/SVGZ | Rasterized through an available ImageMagick SVG decoder |
| JPEG XL, EXR, DPX, CIN, MNG | Extra decoders checked with generated test files |
| AVIF | Native decoding checked for simple still images and animations |
| RAW, DICOM, XCF, WPG | Decoders reported by the system; variants not comprehensively tested |
| HEIC/HEIF | Not supported in the reference configuration |

For a multipage file, Bildblick shows the current page or frame. **Save As** exports only that page, preventing accidental overwrite of the original multipage source.

**File → Export All Pages** combines the currently edited page with the remaining original pages. TIFF, GIF, WebP, and PDF are supported targets. GIF/WebP require identical frame sizes. Animated outputs loop continuously.

There is no document model for maintaining arbitrary separately edited pages at once. A multipage export does not mark the single-page edit state as saved.

## Data storage and limitations

Bildblick processes images locally. It has no account requirement, cloud upload, telemetry client, or automatic update download. External decoders are invoked as local processes.

Output files are first written completely to a temporary file in the destination directory. Only then is the result published. Replacing an existing file requires confirmation in the dialog; batch processing never overwrites existing targets.

Current limitations:

- Editing uses 8-bit RGBA internally; there are no layers or full HDR/16-bit workflow.
- Up to 20 undo steps are kept, reduced when large images reach the memory budget.
- Resizing and standard image loading are limited to 80 megapixels; native extra decoders may impose stricter limits.
- Native decoders limit runtime, memory, and file size; large inputs may be rejected.
- Vector graphics and PDF pages are rasterized. External relative SVG resources are not included.
- AVIF auxiliary images and some alpha variants are not fully supported.
- No validated, monitor-profiled color-management workflow.
- JPEG is re-encoded; lossless JPEG rotation and automatic detection of original quality are not available.
- No layers, advanced brush library, screen capture, or seamless panorama stitching.
- Scanning and media require optional system modules; Windows plugins and executable slideshows are unsupported.
- Physical printing, scanner hardware, media codecs, and complete desktop/accessibility checks have not yet been manually confirmed.

## Development and tests

### Project structure

| File/folder | Purpose |
| --- | --- |
| `bildblick.py` | Window, canvas, open/save, and input handling |
| `editor_ui.py`, `ui_theme.py`, `adjustments.py`, `edit_controls.py` | Styling, sliders, direct selection, and image adjustments |
| `advanced_ui.py`, `menus.py` | Menu actions, navigation, dialogs, and background jobs |
| `image_tools.py`, `tool_dialogs.py`, `file_tools_ui.py`, `paint_dialog.py` | Selection, pixel tools, DPI/printing, file actions, drawing, and optional system integration |
| `image_model.py` | Image state, editing, undo/redo, and page export |
| `image_export.py`, `save_options.py`, `save_dialog.py` | Encoder options, profiles, and save dialog |
| `resize_settings.py`, `resize_dialog.py` | Resize calculations and dialog |
| `native_codecs.py` | Bounded calls to extra decoders |
| `batch.py`, `cli.py` | Job planning and batch processing |
| `assets/` | Kingfisher icon and asset documentation |
| `packaging/` | User install, package builds, and publication |
| `tests/` | Model, controller, export, and decoder checks |

### Automated tests

```bash
/usr/bin/python3 -m unittest discover -s tests -v
```

The current suite contains **114 tests**. It checks actual output files, pixel operations, JPEG options, GIF transparency, metadata controls, profiles, destination collisions, and native decoders. Codec-dependent checks may be skipped on other systems.

### Graphical integration test

```bash
PYTHONPATH=. GDK_BACKEND=x11 GSK_RENDERER=cairo xvfb-run -a \
  -s '-screen 0 1280x900x24' /usr/bin/python3 tests/ui_smoke.py
```

This test needs a graphical environment. Without a display it exits with status `77`, rather than reporting a pass. The local development environment does not allow display access. GitHub Actions runs it with Xvfb and Openbox and provides screenshots as a workflow artifact. It also checks preview, reset, reduced-size export, and a compact window. Further checks cover cm/DPI, selection edges and movement, clipboard, borders, fine rotation, text, gamma/RGB, settings, PDF printing, renaming, and drawing. A complete screen reader, scanner, and physical printer review is still pending.

### Build packages

```bash
/usr/bin/python3 packaging/build.py
```

The build creates `dist/Bildblick-0.11.2-linux.tar.gz` and its SHA-256 file. GitHub Actions also builds the x86-64 AppImage and Flatpak bundle. The source archive includes checksums for its files; user data and export profiles are not packaged.

The GitHub workflow checks changes on `main` in a Fedora container, builds packages, and publishes a prerelease if the version tag does not already have a release. Existing release files are not replaced. For future versions, update the version numbers in the package builder, publication script, workflow, and release notes together.

## Report issues and contribute

When reporting a bug, include your distribution, Python/GTK/Pillow versions, image format, expected behavior, and reproducible steps. Share sample files only if you want to make them public; image metadata may contain personal information.

Contributions should address a clear use case and include suitable checks. Feature claims should distinguish between implemented, automatically tested, and manually verified behavior. The [product document](PRODUCT.md) describes the next development steps.

## License and third-party components

Bildblick is released under the [MIT License](LICENSE). Installed libraries and optional decoders remain separate components under their respective licenses; they are not bundled in the system package.

## Design reference

The local [design reference](design-system/index.html) is an offline HTML/CSS/TypeScript site showing component families, states, and complete dialog examples. [DESIGN.md](design-system/DESIGN.md) and [tokens.json](design-system/tokens.json) define the styling for new and updated parts of the app. Read the project-wide [AGENTS.md](AGENTS.md) before UI changes. See [design-system/README.md](design-system/README.md) for usage and development.

### Consistent interfaces

Dialog width is based on the number of controls and height on natural content. Screen space limits dialog dimensions; dialogs should show their controls without scrolling whenever there is enough room. The [sizing rules](docs/DIALOG-SIZING.md) and [UI audit](docs/UI-AUDIT.md) describe the formula, inventory, and exceptions for native system dialogs.

Short messages and unsaved-change prompts remain compact. **Save**, **Discard**, and **Cancel** are separate actions. A cancelled or failed save never discards changes.

## Design knowledge and ongoing redesign

[knowlede.md](knowlede.md) summarizes the design principles and their application to Bildblick. [redesign.md](redesign.md) records the surface audit, the first implementation pass, and remaining work. The [local HTML reference](design-system/index.html) is the canonical component reference.

Version 0.11.2 adds an x86-64 AppImage alongside Flatpak. Version 0.11.1 fixes missing design tokens in the Flatpak package that prevented startup. Version 0.11.0 adds a Flatpak package for common x86-64 Linux distributions. Version 0.10.0 improved visual hierarchy with clear selection states, grouped fields, a visible save destination, organized image information, and useful empty thumbnail lists.
