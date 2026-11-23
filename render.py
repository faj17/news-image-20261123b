#!/usr/bin/env python3
"""Draw "The World Today" — a one-page broadsheet front page summing up
Monday, 23 November 2026 — as a 1024x1024 PNG.

Every story on the page traces to a sourced item in RESEARCH.md (56 stories
verified 22 Nov 2026; 34 used here). Claims are worded as claims; events
due on Monday are phrased as due, never as results.

Run:  python3 render.py            -> writes entry.png next to this file
      python3 render.py out.png    -> writes to the given path
Deterministic: fixed seed, no clock, no network, stdlib + Pillow only.
"""
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
PAPER = (246, 241, 229)
INK = (22, 21, 19)
RED = (160, 30, 30)
GREY = (90, 86, 78)
RULE = (120, 112, 96)
SPECKLE = (214, 206, 188)
SEED = 20261123
N_SPECKLES = 2600

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")

MASTHEAD = "THE WORLD TODAY"
DATELINE = "Monday, 23 November 2026"
KICKER = "CLIMATE \u2014 ANTALYA, TURKEY"
HEADLINE = "COP31 COLLAPSES AS NO DEAL IS ADOPTED"
SUBHEAD = (
    "Two weeks of talks end in disarray as the EU rejects the final draft; "
    "the text omits the words \u201cfossil fuels\u201d entirely."
)

# (section, headline, one-line summary) per column, in page order.
COLUMNS = [
    [
        ("WAR IN UKRAINE",
         "Russia launches 186 drones at Ukraine overnight",
         "Kyiv says 161 downed; impacts at 18 sites."),
        ("WAR IN UKRAINE",
         "NATO emergency meeting on Monday over Poland",
         "Council to discuss the airspace incursion."),
        ("WAR IN UKRAINE",
         "Russian cargo ship hit by drones, catches fire",
         "Sparta II drifts into Finnish waters."),
        ("WAR IN UKRAINE",
         "Odesa schools go remote as grid is crippled",
         "Remote learning 23\u201327 Nov after strikes."),
        ("MIDDLE EAST",
         "Hamas demands talks after aid workers killed",
         "Strike on food-aid van kills three in Gaza."),
        ("MIDDLE EAST",
         "Gaza flooding displaces 100,000 more people",
         "Oxfam warns; shelter materials blocked."),
        ("MIDDLE EAST",
         "Eisenkot invites Likud to coalition talks",
         "Bid for \u201cbroadest possible government\u201d."),
        ("EUROPE",
         "May urges Burnham to \u201caccept Brexit\u201d",
         "PM to address the Commons on Monday."),
    ],
    [
        ("ASIA-PACIFIC",
         "Indonesia factory fire: 3 dead, 36 missing",
         "Search under way at candy plant in Banten."),
        ("ASIA-PACIFIC",
         "Hong Kong vote sets record 98.79% turnout",
         "Election Committee poll beats 2021 record."),
        ("ASIA-PACIFIC",
         "Korea minister quits over exam-cheating chaos",
         "111 suspected cases before college test."),
        ("ASIA-PACIFIC",
         "Nepal PM arrives in India for state visit",
         "Talks with Modi due on Monday."),
        ("ASIA-PACIFIC",
         "Australia hits back at CBO over AUKUS",
         "Marles defends submarine pact."),
        ("AMERICAS",
         "Trump attacks Cornyn over blocked judge pick",
         "Senator refuses to return the blue slip."),
        ("AMERICAS",
         "Argentina approves $51bn YPF LNG project",
         "Vaca Muerta gas for export, 12m tonnes a year."),
        ("ASIA-PACIFIC",
         "Singapore, China to hold JCBC on Monday",
         "20+ deliverables expected from talks."),
    ],
    [
        ("BUSINESS & TECH",
         "Bitcoin rebounds from ~$55,000 after rout",
         "$2.7bn in leveraged positions liquidated."),
        ("BUSINESS & TECH",
         "Nasdaq suffers worst week since March 2020",
         "AI sell-off erases all of 2026\u2019s gains."),
        ("BUSINESS & TECH",
         "Nvidia falls 22.9% in a week on SEC probe",
         "Reports say US regulator is investigating."),
        ("BUSINESS & TECH",
         "Tesla rolls out FSD v15 with Reality View",
         "First wave of US customers gets update."),
        ("BUSINESS & TECH",
         "US approved 879,868 AI chips for China",
         "Licences, not shipments, House data show."),
        ("SPACE, WEATHER & SPORT",
         "Verstappen wins Las Vegas Grand Prix",
         "Norris second, Piastri third in 50-lap race."),
        ("SPACE, WEATHER & SPORT",
         "SpaceX launches NROL-136 spy satellites",
         "Falcon 9 lifts off from Vandenberg."),
        ("SPACE, WEATHER & SPORT",
         "Tropical Cyclone Xavier churns in Pacific",
         "40 kt winds near Pago Pago; holds to 23 Nov."),
    ],
]

# Bottom strip: (section, headline) per mini-column, round-robin order
# of the nine strip items in RESEARCH.md.
STRIP = [
    [
        ("SPACE, WEATHER & SPORT",
         "Ariane 6 to launch 36 Amazon Leo satellites on Monday"),
        ("SPACE, WEATHER & SPORT",
         "Pant hits 128 as India lead by 307 in Wellington"),
        ("AFRICA", "Somalia\u2019s deadline for UAE envoy expires"),
    ],
    [
        ("SPACE, WEATHER & SPORT",
         "ATP Finals: Alcaraz faces Zverev in Sunday final"),
        ("MIDDLE EAST", "Gaza ceasefire strained as two die of wounds"),
        ("ASIA-PACIFIC", "BMKG warns of heavy rain in eight provinces"),
    ],
    [
        ("SPACE, WEATHER & SPORT",
         "Leeds stun Chelsea 4\u20131; Arsenal stay top"),
        ("AFRICA", "Sudan condemns RSF execution of soldiers"),
        ("AFRICA", "Four-nation summit opens in Oyo, Congo"),
    ],
]

FOOTER = (
    "All stories reported on Sunday, 22 November 2026, for Monday, "
    "23 November 2026 \u00b7 Sources: Reuters, AP, AFP, BBC, Al Jazeera, "
    "CNN, Straits Times, Yonhap, IANS, TipRanks, Formula1.com, "
    "Arianespace, JTWC, NWS"
)

COL_X = (36, 361, 686)
COL_W = 301
TEXT_LEFT, TEXT_RIGHT = 36, 988


def font(name, size):
    return ImageFont.truetype(str(FONT_DIR / name), size)


def wrap(draw, text, fnt, width):
    """Greedy word wrap; returns a list of lines that fit `width`."""
    lines, cur = [], ""
    for word in text.split(" "):
        trial = word if not cur else cur + " " + word
        if draw.textlength(trial, font=fnt) <= width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def render(path):
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    f_mast = font("DejaVuSerif-Bold.ttf", 76)
    f_date = font("DejaVuSerif-Bold.ttf", 20)
    f_kick = font("DejaVuSans-Bold.ttf", 13)
    f_head = font("DejaVuSerif-Bold.ttf", 38)
    f_sub = font("DejaVuSerif.ttf", 14)
    f_sect = font("DejaVuSans-Bold.ttf", 13)
    f_story = font("DejaVuSerif-Bold.ttf", 14)
    f_sum = font("DejaVuSans.ttf", 11)
    f_strip_sect = font("DejaVuSans-Bold.ttf", 12)
    f_strip = font("DejaVuSerif-Bold.ttf", 14)
    f_foot = font("DejaVuSans.ttf", 10)

    # --- Header -------------------------------------------------------
    d.text((W // 2, 10), MASTHEAD, font=f_mast, fill=INK, anchor="ma")
    d.text((W // 2, 100), DATELINE, font=f_date, fill=INK, anchor="ma")
    d.line([(TEXT_LEFT, 130), (TEXT_RIGHT, 130)], fill=RULE, width=1)
    d.rectangle([TEXT_LEFT, 135, TEXT_RIGHT, 136], fill=RED)

    # --- Lead ---------------------------------------------------------
    y = 150
    d.text((TEXT_LEFT, y), KICKER, font=f_kick, fill=RED)
    y += 20
    for line in wrap(d, HEADLINE, f_head, TEXT_RIGHT - TEXT_LEFT)[:2]:
        d.text((TEXT_LEFT, y), line, font=f_head, fill=INK)
        y += 46
    for line in wrap(d, SUBHEAD, f_sub, TEXT_RIGHT - TEXT_LEFT)[:2]:
        d.text((TEXT_LEFT, y), line, font=f_sub, fill=GREY)
        y += 19
    y += 6
    d.line([(TEXT_LEFT, y), (TEXT_RIGHT, y)], fill=RULE, width=1)
    y += 10
    body_top = y

    # --- Columns ------------------------------------------------------
    def section_header(x, y, label, fnt, block=20):
        d.rectangle([x, y + 2, x + 8, y + 10], fill=RED)
        d.text((x + 14, y), label, font=fnt, fill=RED)
        return y + block

    def story(x, y, head, summ):
        for line in wrap(d, head, f_story, COL_W)[:2]:
            d.text((x, y), line, font=f_story, fill=INK)
            y += 17
        for line in wrap(d, summ, f_sum, COL_W)[:1]:
            d.text((x, y), line, font=f_sum, fill=GREY)
            y += 14
        return y + 7

    body_bottom = body_top
    for x, stories in zip(COL_X, COLUMNS):
        y = body_top
        current_section = None
        for section, head, summ in stories:
            if section != current_section:
                y = section_header(x, y, section, f_sect)
                current_section = section
            y = story(x, y, head, summ)
        body_bottom = max(body_bottom, y)

    # Vertical rules between the columns, lead-end to body bottom.
    for rx in (349, 674):
        d.line([(rx, body_top), (rx, body_bottom)], fill=RULE, width=1)

    # --- Bottom strip -------------------------------------------------
    y = body_bottom + 2
    d.line([(TEXT_LEFT, y), (TEXT_RIGHT, y)], fill=RULE, width=1)
    y += 10
    strip_top = y
    strip_bottom = strip_top
    for x, items in zip(COL_X, STRIP):
        yy = strip_top
        current_section = None
        for section, head in items:
            if section != current_section:
                # strip section headers use the tighter 18px block
                yy = section_header(x, yy, section, f_strip_sect, block=18)
                current_section = section
            for line in wrap(d, head, f_strip, COL_W)[:2]:
                d.text((x, yy), line, font=f_strip, fill=INK)
                yy += 16
            yy += 5
        strip_bottom = max(strip_bottom, yy)

    # --- Footer -------------------------------------------------------
    y = strip_bottom + 6
    d.line([(TEXT_LEFT, y), (TEXT_RIGHT, y)], fill=RULE, width=1)
    y += 8
    for line in wrap(d, FOOTER, f_foot, TEXT_RIGHT - TEXT_LEFT)[:2]:
        d.text((W // 2, y), line, font=f_foot, fill=GREY, anchor="ma")
        y += 13
    footer_end = y

    # --- Paper speckle (seeded, deterministic) ------------------------
    rng = random.Random(SEED)
    for _ in range(N_SPECKLES):
        d.point((rng.randrange(W), rng.randrange(H)), fill=SPECKLE)

    img.save(path, optimize=True)
    print(f"body_top={body_top} body_bottom={body_bottom} "
          f"strip_bottom={strip_bottom} footer_end={footer_end}")
    return footer_end


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "entry.png"
    render(out)
    print(f"wrote {out} ({out.stat().st_size} bytes)")
