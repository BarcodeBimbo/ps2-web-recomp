from PIL import Image, ImageDraw, ImageChops, ImageEnhance
import os

live_path = r"c:\PS2Recomp\jarvis-cursor-ui\media\image.png"
ref_path = r"c:\PS2Recomp\jarvis-cursor-ui\media\reference-command-center-2.png"
out = r"c:\PS2Recomp\jarvis-cursor-ui\media\inject\_audit_deep"
os.makedirs(out, exist_ok=True)

live = Image.open(live_path).convert("RGBA")
ref = Image.open(ref_path).convert("RGBA")

ref_scaled = ref.resize(live.size, Image.Resampling.LANCZOS)
live_rgb = live.convert("RGB")
ref_rgb = ref_scaled.convert("RGB")

diff = ImageChops.difference(live_rgb, ref_rgb)
diff_e = ImageEnhance.Brightness(diff).enhance(3.0)
diff_e.save(os.path.join(out, "00_diff_heatmap.png"))

ss = Image.new("RGB", (live.width * 2 + 20, live.height + 40), (10, 14, 20))
ss.paste(live_rgb, (0, 30))
ss.paste(ref_rgb, (live.width + 20, 30))
d = ImageDraw.Draw(ss)
d.text((10, 5), "LIVE", fill=(0, 229, 255))
d.text((live.width + 30, 5), "REF (scaled)", fill=(0, 229, 255))
ss.save(os.path.join(out, "00_side_by_side.png"))

regions = {
    "01_header": (0.0, 0.0, 1.0, 0.10),
    "02_header_left": (0.0, 0.0, 0.28, 0.10),
    "03_header_center": (0.28, 0.0, 0.62, 0.10),
    "04_header_right": (0.62, 0.0, 1.0, 0.10),
    "05_sidebar_nav": (0.0, 0.10, 0.16, 0.55),
    "06_sidebar_voice": (0.0, 0.55, 0.16, 0.82),
    "07_sidebar_focus": (0.0, 0.82, 0.16, 0.92),
    "08_ai_core_overview": (0.16, 0.10, 0.42, 0.38),
    "09_center_globe": (0.42, 0.10, 0.70, 0.42),
    "10_intel_feed": (0.70, 0.10, 1.0, 0.38),
    "11_active_agents": (0.16, 0.38, 0.42, 0.68),
    "12_mission_timeline": (0.42, 0.42, 0.70, 0.68),
    "13_quick_commands": (0.70, 0.38, 1.0, 0.62),
    "14_system_monitor": (0.16, 0.68, 0.42, 0.90),
    "15_memory_insights": (0.42, 0.68, 0.70, 0.90),
    "16_llm_status": (0.70, 0.62, 1.0, 0.90),
    "17_bottom_bar": (0.0, 0.90, 1.0, 1.0),
    "18_bottom_left": (0.0, 0.90, 0.28, 1.0),
    "19_bottom_center": (0.28, 0.90, 0.72, 1.0),
    "20_bottom_right": (0.72, 0.90, 1.0, 1.0),
}


def crop_frac(im, frac):
    w, h = im.size
    l, t, r, b = frac
    box = (int(l * w), int(t * h), int(r * w), int(b * h))
    return im.crop(box), box


for name, frac in regions.items():
    cl, _ = crop_frac(live, frac)
    cr, _ = crop_frac(ref, frac)
    cr2 = cr.resize(cl.size, Image.Resampling.LANCZOS)
    pair = Image.new("RGB", (cl.width * 2 + 10, cl.height + 24), (8, 12, 18))
    pair.paste(cl.convert("RGB"), (0, 20))
    pair.paste(cr2.convert("RGB"), (cl.width + 10, 20))
    dd = ImageDraw.Draw(pair)
    dd.text((2, 2), f"LIVE {name}", fill=(0, 229, 255))
    dd.text((cl.width + 12, 2), f"REF {name}", fill=(255, 180, 0))
    pair.save(os.path.join(out, f"{name}_pair.png"))
    cl.save(os.path.join(out, f"{name}_live.png"))
    cr_native, _ = crop_frac(ref, frac)
    cr_native.save(os.path.join(out, f"{name}_ref.png"))

# Zoomed native ref full + live downscaled side-by-side for layout
live_to_ref = live.resize(ref.size, Image.Resampling.LANCZOS)
pair2 = Image.new("RGB", (ref.width * 2 + 10, ref.height + 24), (8, 12, 18))
pair2.paste(live_to_ref.convert("RGB"), (0, 20))
pair2.paste(ref.convert("RGB"), (ref.width + 10, 20))
dd = ImageDraw.Draw(pair2)
dd.text((2, 2), "LIVE->REF size", fill=(0, 229, 255))
dd.text((ref.width + 12, 2), "REF native", fill=(255, 180, 0))
pair2.save(os.path.join(out, "00_side_by_side_refsize.png"))

print("live", live.size, "ref", ref.size)
print("ok")
