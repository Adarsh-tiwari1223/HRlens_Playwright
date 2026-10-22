"""
Generator for Transparent Realistic Signatures of Branch Heads.
Target Directory: C:\\Users\\User\\Desktop\\Tekinspirations\\HRlens_Playwright\\testdata\\static\\image\\Signature

Features:
- 100% True Transparent PNG (RGBA)
- Stylized handwritten/cursive signature strokes with ink flourishes
- Base signatures for all 8 Branch Heads:
    1. Brij Rawat (Agra)
    2. Vivek Singh (Varanasi)
    3. Arvind Kumar (Meerut)
    4. Satish Singh (Noida)
    5. Davesh Sharma (Noida Ops)
    6. Yatendra Rawat (Greater Noida)
    7. Riyan Sharma (Agra Sales)
    8. Gagan Pradhan (Bhubaneswar)
- Boundary Value Test Signatures for File Limit Testing (100KB to 5.1MB):
    - 100 KB  (Valid Nominal)
    - 1.0 MB  (Valid Standard)
    - 2.0 MB  (Valid Mid)
    - 4.9 MB  (Valid Max - Δ)
    - 5.0 MB  (Valid Boundary Threshold)
    - 5.1 MB  (Invalid Boundary Breach for DEF_024)
"""

import os
import io
import struct
import zlib
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = os.path.abspath(r"testdata\static\image\Signature")
os.makedirs(OUTPUT_DIR, exist_ok=True)

BRANCH_HEADS = [
    {"name": "Brij Rawat", "filename": "signature_brij_rawat.png", "title": "Director & Branch Head (Agra)"},
    {"name": "Vivek Singh", "filename": "signature_vivek_singh.png", "title": "Branch Head (Varanasi)"},
    {"name": "Arvind Kumar", "filename": "signature_arvind_kumar.png", "title": "Branch Head (Meerut)"},
    {"name": "Satish Singh", "filename": "signature_satish_singh.png", "title": "Branch Head (Noida)"},
    {"name": "Davesh Sharma", "filename": "signature_davesh_sharma.png", "title": "Operations Head (Noida)"},
    {"name": "Yatendra Rawat", "filename": "signature_yatendra_rawat.png", "title": "Sales Head (Greater Noida)"},
    {"name": "Riyan Sharma", "filename": "signature_riyan_sharma.png", "title": "Sales Head (Agra)"},
    {"name": "Gagan Pradhan", "filename": "signature_gagan_pradhan.png", "title": "Branch Head (Bhubaneswar)"},
]

BOUNDARY_SIZES = [
    {"suffix": "100kb", "bytes": 100 * 1024},
    {"suffix": "1mb", "bytes": 1024 * 1024},
    {"suffix": "2mb", "bytes": 2 * 1024 * 1024},
    {"suffix": "4_9mb", "bytes": int(4.9 * 1024 * 1024)},
    {"suffix": "5mb", "bytes": 5 * 1024 * 1024},
    {"suffix": "5_1mb", "bytes": int(5.1 * 1024 * 1024)},
]


def create_transparent_signature_image(name: str, width=600, height=220) -> Image.Image:
    """Creates a transparent RGBA image with handwritten-style cursive pen strokes."""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Try loading cursive or elegant script font from Windows Fonts, fallback to default
    font_candidates = [
        "C:\\Windows\\Fonts\\segoesc.ttf",  # Segoe Script
        "C:\\Windows\\Fonts\\segoescb.ttf", # Segoe Script Bold
        "C:\\Windows\\Fonts\\FREESCPT.TTF", # French Script
        "C:\\Windows\\Fonts\\SCRIPTBL.TTF", # Script Bold
        "C:\\Windows\\Fonts\\ariali.ttf",   # Arial Italic
    ]

    font = None
    for f_path in font_candidates:
        if os.path.exists(f_path):
            try:
                font = ImageFont.truetype(f_path, 48)
                break
            except Exception:
                continue

    if not font:
        font = ImageFont.load_default()

    # Dark executive navy blue ink: RGBA(15, 37, 72, 255)
    ink_color = (15, 37, 72, 245)

    # Draw cursive signature text
    text_x = 45
    text_y = 50
    draw.text((text_x, text_y), name, fill=ink_color, font=font)

    # Add realistic flourish curve / underline loops
    bbox = draw.textbbox((text_x, text_y), name, font=font)
    line_start_x = text_x - 10
    line_end_x = bbox[2] + 40
    line_y = bbox[3] + 10

    # Underline strokes with taper
    draw.line([(line_start_x, line_y), (line_end_x - 20, line_y + 4)], fill=ink_color, width=3)
    draw.arc([line_end_x - 40, line_y - 12, line_end_x + 15, line_y + 16], start=300, end=90, fill=ink_color, width=2)
    draw.line([(line_end_x - 10, line_y + 12), (line_end_x - 60, line_y + 20)], fill=ink_color, width=2)

    return img


def add_png_padding(png_bytes: bytes, target_size: int) -> bytes:
    """
    Appends a standard auxiliary uncompressed tEXt chunk to achieve the exact target byte size.
    The image remains 100% valid, transparent, and renderable by any browser or image viewer.
    """
    current_size = len(png_bytes)
    if current_size >= target_size:
        return png_bytes

    # PNG structure: Signature (8 bytes) ... IEND (12 bytes at end)
    # Insert custom 'tEXt' chunk just before IEND
    iend_pos = png_bytes.rfind(b"IEND")
    if iend_pos == -1:
        # Fallback: simple trailing padding
        return png_bytes + b"\x00" * (target_size - current_size)

    # Target chunk overhead: Length (4) + ChunkType (4) + Keyword + Null (8) + CRC (4) = 20 bytes
    needed_bytes = target_size - current_size
    chunk_type = b"tEXt"
    keyword = b"Comment\x00"
    payload_len = max(0, needed_bytes - 12 - len(keyword))
    payload = b"X" * payload_len

    chunk_data = keyword + payload
    crc = zlib.crc32(chunk_type + chunk_data) & 0xffffffff
    chunk = struct.pack(">I", len(chunk_data)) + chunk_type + chunk_data + struct.pack(">I", crc)

    padded = png_bytes[:iend_pos - 4] + chunk + png_bytes[iend_pos - 4:]
    
    # Fine tune if delta exists
    if len(padded) < target_size:
        padded = padded + b"\x00" * (target_size - len(padded))
    elif len(padded) > target_size:
        # Trim from payload
        diff = len(padded) - target_size
        payload = b"X" * max(0, payload_len - diff)
        chunk_data = keyword + payload
        crc = zlib.crc32(chunk_type + chunk_data) & 0xffffffff
        chunk = struct.pack(">I", len(chunk_data)) + chunk_type + chunk_data + struct.pack(">I", crc)
        padded = png_bytes[:iend_pos - 4] + chunk + png_bytes[iend_pos - 4:]

    return padded


def generate_all():
    print("=" * 80)
    print("GENERATING TRANSPARENT BRANCH HEAD SIGNATURE TEST ASSETS")
    print(f"Output Directory: {OUTPUT_DIR}")
    print("=" * 80)

    # 1. Generate base transparent signatures for all 8 Branch Heads
    for bh in BRANCH_HEADS:
        img = create_transparent_signature_image(bh["name"])
        out_path = os.path.join(OUTPUT_DIR, bh["filename"])
        img.save(out_path, format="PNG")
        file_size = os.path.getsize(out_path)
        print(f"[BASE SIGNATURE] {bh['name']:<18} -> {bh['filename']:<30} | {file_size:>7} bytes | {bh['title']}")

    # 2. Generate calibrated Boundary Value Analysis (BVA) files for file limit testing
    print("\n" + "-" * 80)
    print("GENERATING BOUNDARY SIZED SIGNATURES (100KB to 5.1MB)")
    print("-" * 80)

    base_brij_img = create_transparent_signature_image("Brij Rawat")
    buffer = io.BytesIO()
    base_brij_img.save(buffer, format="PNG")
    raw_bytes = buffer.getvalue()

    for bva in BOUNDARY_SIZES:
        filename = f"signature_brij_rawat_{bva['suffix']}.png"
        out_path = os.path.join(OUTPUT_DIR, filename)
        padded_bytes = add_png_padding(raw_bytes, bva["bytes"])
        with open(out_path, "wb") as f:
            f.write(padded_bytes)
        actual_size = os.path.getsize(out_path)
        mb_size = actual_size / (1024 * 1024)
        print(f"[BVA ASSET] {filename:<32} -> Target: {bva['bytes']:>10} bytes | Actual: {actual_size:>10} bytes ({mb_size:.2f} MB)")

    print("\n" + "=" * 80)
    print("ALL SIGNATURE TEST IMAGES SUCCESSFULLY CREATED")
    print("=" * 80)


if __name__ == "__main__":
    generate_all()
