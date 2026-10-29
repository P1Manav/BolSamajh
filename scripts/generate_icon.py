"""Generate multi-resolution BolSamajh application icon (assets/bolsamajh.ico)."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def generate_icon():
    root = Path(__file__).resolve().parent.parent
    assets_dir = root / "assets"
    assets_dir.mkdir(exist_ok=True)
    ico_path = assets_dir / "bolsamajh.ico"
    png_path = assets_dir / "bolsamajh.png"

    sizes = [16, 24, 32, 48, 64, 128, 256]
    images = []

    for size in sizes:
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Draw anti-aliased rounded blue microphone circle
        padding = max(1, size // 16)
        draw.ellipse([padding, padding, size - padding, size - padding], fill=(59, 130, 246, 255))

        # Draw white 'B'
        font_size = max(10, size // 2)
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except OSError:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), "B", font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        x = (size - tw) / 2
        y = (size - th) / 2 - (size // 16)
        draw.text((x, y), "B", fill=(255, 255, 255, 255), font=font)
        images.append(img)

    # Save highest resolution PNG
    images[-1].save(png_path, format="PNG")

    # Save multi-size ICO
    images[-1].save(
        ico_path,
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=images[:-1],
    )
    print(f"Generated {ico_path} and {png_path} successfully.")


if __name__ == "__main__":
    generate_icon()
