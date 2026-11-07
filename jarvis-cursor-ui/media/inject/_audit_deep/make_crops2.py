from PIL import Image, ImageDraw
import os

out = r"c:\PS2Recomp\jarvis-cursor-ui\media\inject\_audit_deep"
live = Image.open(r"c:\PS2Recomp\jarvis-cursor-ui\media\image.png").convert("RGBA")
ref = Image.open(r"c:\PS2Recomp\jarvis-cursor-ui\media\reference-command-center-2.png").convert("RGBA")

# Absolute pixel boxes tuned from visual inspection of each image
# LIVE 1598x899
live_boxes = {
    "L_header": (0, 0, 1598, 78),
    "L_brand": (8, 8, 280, 70),
    "L_status": (280, 8, 520, 55),
    "L_clock": (560, 5, 980, 72),
    "L_search": (1000, 12, 1280, 55),
    "L_ops": (1280, 8, 1520, 65),
    "L_sidebar": (0, 78, 220, 820),
    "L_nav": (8, 78, 215, 480),
    "L_voice": (8, 480, 215, 720),
    "L_focus": (8, 720, 215, 800),
    "L_ai_overview": (230, 85, 560, 320),
    "L_globe": (560, 85, 1050, 360),
    "L_intel": (1050, 85, 1585, 320),
    "L_agents": (230, 325, 560, 580),
    "L_timeline": (560, 365, 1050, 580),
    "L_quick": (1050, 325, 1585, 520),
    "L_sysmon": (230, 585, 560, 800),
    "L_memory": (560, 585, 1050, 800),
    "L_llm": (1050, 525, 1585, 800),
    "L_footer": (0, 800, 1598, 899),
    "L_talk": (450, 810, 1150, 890),
    "L_brief": (1250, 820, 1580, 885),
    "L_footer_left": (10, 810, 430, 890),
}

# REF 1024x573 - approximate from description
ref_boxes = {
    "R_header": (0, 0, 1024, 55),
    "R_brand": (5, 5, 220, 48),
    "R_status": (230, 8, 420, 45),
    "R_clock": (420, 2, 620, 52),
    "R_search": (620, 10, 820, 42),
    "R_ops": (820, 5, 1015, 48),
    "R_sidebar": (0, 55, 155, 520),
    "R_nav": (5, 55, 150, 320),
    "R_voice": (5, 320, 150, 470),
    "R_focus": (5, 470, 150, 515),
    "R_ai_overview": (160, 55, 380, 220),
    "R_globe": (380, 55, 680, 250),
    "R_intel": (680, 55, 1015, 220),
    "R_agents": (160, 220, 380, 380),
    "R_timeline": (380, 250, 680, 380),
    "R_quick": (680, 220, 1015, 350),
    "R_sysmon": (160, 380, 380, 510),
    "R_memory": (380, 380, 680, 510),
    "R_llm": (680, 350, 1015, 510),
    "R_footer": (0, 510, 1024, 573),
    "R_talk": (300, 515, 720, 568),
    "R_brief": (780, 520, 1010, 565),
    "R_footer_left": (5, 515, 290, 565),
}

def save_crop(im, box, name, scale=2):
    c = im.crop(box)
    if scale != 1:
        c = c.resize((c.width * scale, c.height * scale), Image.Resampling.NEAREST)
    c.save(os.path.join(out, f"{name}.png"))
    return c

for k, b in live_boxes.items():
    save_crop(live, b, k, 2)

for k, b in ref_boxes.items():
    save_crop(ref, b, k, 2)

# Also save full images at readable height for side annotation
live_s = live.resize((1200, int(1200 * live.height / live.width)), Image.Resampling.LANCZOS)
ref_s = ref.resize((1200, int(1200 * ref.height / ref.width)), Image.Resampling.LANCZOS)
live_s.save(os.path.join(out, "FULL_live_1200.png"))
ref_s.save(os.path.join(out, "FULL_ref_1200.png"))

# Annotated grid overlay to verify boxes
def annotate(im, boxes, prefix, name):
    a = im.convert("RGB").copy()
    d = ImageDraw.Draw(a)
    for k, b in boxes.items():
        if not k.startswith(prefix):
            continue
        d.rectangle(b, outline=(0, 255, 255), width=2)
        d.text((b[0] + 3, b[1] + 3), k, fill=(255, 200, 0))
    a.save(os.path.join(out, name))

annotate(live, live_boxes, "L_", "ANNOT_live.png")
annotate(ref, ref_boxes, "R_", "ANNOT_ref.png")
print("done")
