#!/usr/bin/env python
import argparse
import shutil
import subprocess
from pathlib import Path

from PIL import ImageFont

# text2image defaults
DEFAULT_PTSIZE = 12
DEFAULT_RESOLUTION = 300
DEFAULT_LEADING = 12
DEFAULT_MARGIN = 100
DEFAULT_FONT = "Noto Sans Devanagari"


def resolve_font_path(font_name):
    """Use fc-match to find the actual .ttf/.otf file for a font name."""
    try:
        result = subprocess.run(
            ["fc-match", "--format=%{file}", font_name],
            capture_output=True,
            text=True,
            check=True,
        )
        path = result.stdout.strip()
        if path and Path(path).exists():
            return path
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return None


def compute_dimensions(txt_path, font_name, ptsize, resolution, leading, margin):
    """Compute the tightest xsize/ysize for the text so lines don't wrap.

    Uses Pillow to measure the rendered text width/height, converting the
    typographic point size + DPI into an equivalent pixel size the same way
    text2image (Pango) does: pixel_size = ptsize * dpi / 72.

    Returns (xsize, ysize).
    """
    font_path = resolve_font_path(font_name)
    if font_path is None:
        print(
            f"  Warning: Could not resolve font '{font_name}' via fc-match, "
            "falling back to default dimensions."
        )
        return None, None

    pixel_size = int(ptsize * resolution / 72)
    font = ImageFont.truetype(font_path, pixel_size)

    lines = txt_path.read_text(encoding="utf-8").splitlines()
    # Drop trailing empty lines
    while lines and lines[-1].strip() == "":
        lines.pop()

    if not lines:
        return None, None

    max_width = 0
    for line in lines:
        if not line:
            # Empty lines still take vertical space but have zero width
            continue
        bbox = font.getbbox(line)
        w = bbox[2] - bbox[0]
        if w > max_width:
            max_width = w

    ascent, descent = font.getmetrics()
    line_height = ascent + descent
    num_lines = len(lines)
    total_height = num_lines * line_height + max(0, num_lines - 1) * leading

    # Add margins and a small safety buffer (10%) to account for minor
    # rendering differences between Pillow and Pango.
    xsize = int((max_width + 2 * margin) * 1.1)
    ysize = int((total_height + 2 * margin) * 1.1)

    # text2image can misbehave with very small images; enforce minimums
    xsize = max(xsize, 200)
    ysize = max(ysize, 200)

    return xsize, ysize


def build_command(
    txt_file,
    output_base,
    font,
    ptsize,
    resolution,
    leading,
    margin,
    char_spacing,
    xsize,
    ysize,
    exposure,
    degrade_image,
    rotate_image,
    distort_image,
    invert,
    white_noise,
    smooth_noise,
    blur,
    bidirectional_rotation,
):
    """Build the text2image command list."""
    cmd = [
        "text2image",
        f"--text={txt_file}",
        f"--outputbase={output_base}",
        f"--font={font}",
        f"--ptsize={ptsize}",
        f"--resolution={resolution}",
        f"--leading={leading}",
        f"--margin={margin}",
        f"--char_spacing={char_spacing}",
        f"--xsize={xsize}",
        f"--ysize={ysize}",
        f"--exposure={exposure}",
    ]

    # Boolean flags -- text2image expects --flag=true / --flag=false
    bool_flags = {
        "degrade_image": degrade_image,
        "rotate_image": rotate_image,
        "distort_image": distort_image,
        "invert": invert,
        "white_noise": white_noise,
        "smooth_noise": smooth_noise,
        "blur": blur,
        "bidirectional_rotation": bidirectional_rotation,
    }
    for flag, value in bool_flags.items():
        cmd.append(f"--{flag}={'true' if value else 'false'}")

    return cmd


def process_folder(
    folder_path,
    output_dir=None,
    font=DEFAULT_FONT,
    ptsize=DEFAULT_PTSIZE,
    resolution=DEFAULT_RESOLUTION,
    leading=DEFAULT_LEADING,
    margin=DEFAULT_MARGIN,
    char_spacing=0.0,
    exposure=0,
    degrade_image=True,
    rotate_image=True,
    distort_image=False,
    invert=True,
    white_noise=True,
    smooth_noise=True,
    blur=True,
    bidirectional_rotation=False,
):
    folder = Path(folder_path).resolve()

    if not folder.exists():
        print(f"Error: Folder '{folder}' does not exist.")
        return

    # Determine output directory
    if output_dir is None:
        out = folder / "output"
    else:
        out = Path(output_dir).resolve()

    out.mkdir(parents=True, exist_ok=True)

    txt_files = sorted(folder.glob("*.txt"))

    if not txt_files:
        print(f"No .txt files found in '{folder}'.")
        return

    for txt_file in txt_files:
        print(f"\nProcessing: {txt_file.name}")

        base_name = txt_file.stem
        output_base = out / base_name

        # --- Dynamic sizing ---
        xsize, ysize = compute_dimensions(
            txt_file, font, ptsize, resolution, leading, margin
        )
        if xsize is None or ysize is None:
            print("  Skipping (empty file or font resolution failed).")
            continue

        print(f"  Computed dimensions: {xsize}x{ysize} (ptsize={ptsize})")

        cmd = build_command(
            txt_file=txt_file,
            output_base=output_base,
            font=font,
            ptsize=ptsize,
            resolution=resolution,
            leading=leading,
            margin=margin,
            char_spacing=char_spacing,
            xsize=xsize,
            ysize=ysize,
            exposure=exposure,
            degrade_image=degrade_image,
            rotate_image=rotate_image,
            distort_image=distort_image,
            invert=invert,
            white_noise=white_noise,
            smooth_noise=smooth_noise,
            blur=blur,
            bidirectional_rotation=bidirectional_rotation,
        )

        try:
            print(f"  Running: {' '.join(cmd)}")
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"  Error running text2image on {txt_file.name}: {e}")
            continue
        except FileNotFoundError:
            print(
                "  Error: 'text2image' command not found. "
                "Are the Tesseract training tools installed?"
            )
            return

        # Copy the source text file as ground truth (.gt.txt)
        gt_file = output_base.with_suffix(".gt.txt")
        shutil.copy2(txt_file, gt_file)
        print(f"  Ground truth saved to {gt_file.name}")

    print("\nProcessing complete.")


def parse_bool(value):
    """Parse a boolean CLI argument."""
    if value.lower() in ("true", "1", "yes"):
        return True
    if value.lower() in ("false", "0", "no"):
        return False
    raise argparse.ArgumentTypeError(f"Boolean value expected, got '{value}'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate .tif and .box training images from text files using "
        "text2image. Image dimensions are automatically computed to fit "
        "the text content without line wrapping or excessive whitespace.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
examples:
  %(prog)s /path/to/texts
  %(prog)s /path/to/texts --ptsize=14 --font="Arial"
  %(prog)s /path/to/texts --distort-image --exposure=3
  %(prog)s /path/to/texts --no-degrade --no-rotate  # clean images
""",
    )

    # --- Required ---
    parser.add_argument("folder", help="Path to the folder containing .txt files")

    # --- Output ---
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory to store output files (default: <folder>/output)",
    )

    # --- Rendering ---
    render = parser.add_argument_group("rendering options")
    render.add_argument(
        "--font",
        default=DEFAULT_FONT,
        help=f'Font description name (default: "{DEFAULT_FONT}")',
    )
    render.add_argument(
        "--ptsize",
        type=int,
        default=DEFAULT_PTSIZE,
        help=f"Font point size (default: {DEFAULT_PTSIZE})",
    )
    render.add_argument(
        "--resolution",
        type=int,
        default=DEFAULT_RESOLUTION,
        help=f"Pixels per inch (default: {DEFAULT_RESOLUTION})",
    )
    render.add_argument(
        "--leading",
        type=int,
        default=DEFAULT_LEADING,
        help=f"Inter-line spacing in pixels (default: {DEFAULT_LEADING})",
    )
    render.add_argument(
        "--margin",
        type=int,
        default=DEFAULT_MARGIN,
        help=f"Margin around edges of image in pixels (default: {DEFAULT_MARGIN})",
    )
    render.add_argument(
        "--char-spacing",
        type=float,
        default=0.0,
        help="Inter-character spacing in ems (default: 0)",
    )

    # --- Distortion / Degradation ---
    distort = parser.add_argument_group(
        "distortion options",
        "Control image degradation effects applied by text2image. "
        "Use --flag / --no-flag syntax to toggle boolean options.",
    )
    distort.add_argument(
        "--exposure",
        type=int,
        default=0,
        help="Exposure level in photocopier effect (default: 0)",
    )
    distort.add_argument(
        "--degrade-image",
        default=True,
        action=argparse.BooleanOptionalAction,
        help="Degrade image with speckle noise, dilation/erosion, rotation "
        "(default: on)",
    )
    distort.add_argument(
        "--rotate-image",
        default=True,
        action=argparse.BooleanOptionalAction,
        help="Rotate the image randomly (default: on)",
    )
    distort.add_argument(
        "--distort-image",
        default=False,
        action=argparse.BooleanOptionalAction,
        help="Degrade image with noise, blur, invert (default: off)",
    )
    distort.add_argument(
        "--invert",
        default=True,
        action=argparse.BooleanOptionalAction,
        help="Invert the image colors (default: on)",
    )
    distort.add_argument(
        "--white-noise",
        default=True,
        action=argparse.BooleanOptionalAction,
        help="Add Gaussian white noise (default: on)",
    )
    distort.add_argument(
        "--smooth-noise",
        default=True,
        action=argparse.BooleanOptionalAction,
        help="Smoothen noise (default: on)",
    )
    distort.add_argument(
        "--blur",
        default=True,
        action=argparse.BooleanOptionalAction,
        help="Blur the image (default: on)",
    )
    distort.add_argument(
        "--bidirectional-rotation",
        default=False,
        action=argparse.BooleanOptionalAction,
        help="Rotate generated characters both ways (default: off)",
    )

    args = parser.parse_args()

    process_folder(
        args.folder,
        output_dir=args.output_dir,
        font=args.font,
        ptsize=args.ptsize,
        resolution=args.resolution,
        leading=args.leading,
        margin=args.margin,
        char_spacing=args.char_spacing,
        exposure=args.exposure,
        degrade_image=args.degrade_image,
        rotate_image=args.rotate_image,
        distort_image=args.distort_image,
        invert=args.invert,
        white_noise=args.white_noise,
        smooth_noise=args.smooth_noise,
        blur=args.blur,
        bidirectional_rotation=args.bidirectional_rotation,
    )
