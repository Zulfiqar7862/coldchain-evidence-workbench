"""Generate original conceptual GIF/PNG. Not a recording or UI screenshot."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path("docs/assets")
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except OSError:
        return ImageFont.load_default(size=size)


def image(frame):
    im = Image.new("RGB", (1120, 500), "#f5f7f7")
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, 1119, 499), 16, fill="#102f3c")
    d.text((44, 30), "ONE CASE. TWO INDEPENDENT TRACKS.", font=font(28), fill="#ffffff")
    d.text(
        (44, 78),
        "Conceptual animation · invented teaching example · not recorded UI",
        font=font(15),
        fill="#adc4cd",
    )
    d.text((44, 142), "Evidence track", font=font(20), fill="#b6e7d6")
    d.text((44, 304), "Notification track", font=font(20), fill="#f3d5a1")
    labels = [
        ("Capture", "Verify", "Local QA review"),
        ("Assess status", "Track deadline", "Still PENDING"),
    ]
    positions = [270, 530, 790]
    for lane, y in enumerate([190, 350]):
        for i, x in enumerate(positions):
            if i < 2:
                d.line((x + 190, y + 30, x + 256, y + 30), fill="#5e7e88", width=2)
            color = "#b6e7d6" if lane == 0 else "#f3d5a1"
            active = i <= (frame // 2 if lane == 0 else min(frame // 2, 2))
            d.rounded_rectangle((x, y, x + 205, y + 62), 8, fill=color if active else "#244653")
            d.text(
                (x + 12, y + 19),
                labels[lane][i],
                font=font(17),
                fill="#17353a" if active else "#afc4cd",
            )
    if frame >= 5:
        d.text(
            (270, 266),
            "Review recorded. This does NOT release a product.",
            font=font(15),
            fill="#b6e7d6",
        )
        d.text(
            (270, 430),
            "Still pending after review; only a qualified assessment changes this.",
            font=font(15),
            fill="#f3d5a1",
        )
    return im


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    frames = [image(i) for i in range(7)]
    frames[-1].save(OUT / "two-tracks.png")
    frames[0].save(
        OUT / "two-tracks.gif",
        save_all=True,
        append_images=frames[1:],
        duration=[500] * 6 + [2200],
        loop=0,
        optimize=True,
    )


if __name__ == "__main__":
    main()
