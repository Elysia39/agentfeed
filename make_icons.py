import os
import subprocess
from PIL import Image

src_img_path = "/Users/dabinmac/.gemini/antigravity/brain/abbb76b4-77b1-43fa-a415-a76c52f77637/agentfeed_cute_mascot_head_1787600918350.jpg"
target_dir = "/Users/dabinmac/.gemini/antigravity/scratch/agentfeed"
os.makedirs(os.path.join(target_dir, "assets"), exist_ok=True)

img = Image.open(src_img_path).convert("RGBA")

# Save base PNGs
png_512 = os.path.join(target_dir, "assets", "icon.png")
img.resize((512, 512), Image.Resampling.LANCZOS).save(png_512, format="PNG")
img.resize((512, 512), Image.Resampling.LANCZOS).save(os.path.join(target_dir, "icon.png"), format="PNG")

# Save ICO (Windows)
ico_path = os.path.join(target_dir, "icon.ico")
img.save(ico_path, format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])

# Create macOS ICNS using iconutil
iconset_dir = os.path.join(target_dir, "assets", "icon.iconset")
os.makedirs(iconset_dir, exist_ok=True)

sizes = [16, 32, 64, 128, 256, 512]
for s in sizes:
    img.resize((s, s), Image.Resampling.LANCZOS).save(os.path.join(iconset_dir, f"icon_{s}x{s}.png"))
    img.resize((s*2, s*2), Image.Resampling.LANCZOS).save(os.path.join(iconset_dir, f"icon_{s}x{s}@2x.png"))

icns_path = os.path.join(target_dir, "icon.icns")
subprocess.run(["iconutil", "-c", "icns", iconset_dir, "-o", icns_path], check=True)
print("✅ Applied the chosen mascot cartoon icon (icon.icns, icon.ico, icon.png) successfully!")
