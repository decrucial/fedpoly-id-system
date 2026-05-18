import qrcode, os, uuid, base64
from PIL import Image, ImageDraw, ImageFont
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from flask import current_app

# ── Cipher ─────────────────────────────────────────────────────────────────────
def get_cipher():
    key_material = current_app.config['ENCRYPTION_KEY'].encode()
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32,
                     salt=b'fedpoly_nasarawa_salt_2024', iterations=100000)
    return Fernet(base64.urlsafe_b64encode(kdf.derive(key_material)))

def generate_token(matric):
    return get_cipher().encrypt(f"{matric}|{uuid.uuid4()}".encode()).decode()

def decrypt_token(token):
    try:
        return get_cipher().decrypt(token.encode()).decode().split('|', 1)[0]
    except Exception:
        return None

# ── QR Code ────────────────────────────────────────────────────────────────────
def generate_qr_code(token, matric_number):
    url = f"{current_app.config['BASE_URL']}/verify/{token}"
    qr  = qrcode.QRCode(version=1,
                        error_correction=qrcode.constants.ERROR_CORRECT_H,
                        box_size=10, border=2)
    qr.add_data(url); qr.make(fit=True)
    img = qr.make_image(fill_color="#0d1a5e", back_color="white")
    fn  = f"qr_{matric_number.replace('/', '_')}.png"
    img.save(os.path.join(current_app.config['QR_FOLDER'], fn))
    return fn

# ── Fonts ──────────────────────────────────────────────────────────────────────
_FONTS = [
    ('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
     '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),
    ('/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
     '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'),
    ('/usr/share/fonts/truetype/freefont/FreeSansBold.ttf',
     '/usr/share/fonts/truetype/freefont/FreeSans.ttf'),
]
def fnt(size, bold=False):
    for b, r in _FONTS:
        p = b if bold else r
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except: pass
    return ImageFont.load_default()

def tw(draw, text, font):
    try: return int(draw.textlength(text, font=font))
    except:
        bb = draw.textbbox((0,0), text, font=font)
        return bb[2] - bb[0]

def wrap(draw, text, font, max_w):
    words, lines, cur = text.split(), [], ''
    for w in words:
        test = (cur + ' ' + w).strip()
        if tw(draw, test, font) <= max_w: cur = test
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines or [text]

# ── Colours ────────────────────────────────────────────────────────────────────
NAVY      = ( 13,  26,  94)
NAVY_D    = (  8,  15,  58)
NAVY_L    = ( 26,  40, 112)
GOLD      = (249, 168,  37)
GOLD_L    = (255, 213,  79)
RED       = (198,  40,  40)
WHITE     = (255, 255, 255)
LGREY     = (240, 242, 248)
MGREY     = (180, 185, 210)
DARK      = ( 20,  20,  50)
MID       = ( 90,  95, 125)

def rr(draw, x1, y1, x2, y2, r, fill, outline=None, ow=0):
    """Rounded rectangle."""
    draw.rectangle([x1+r, y1,   x2-r, y2  ], fill=fill)
    draw.rectangle([x1,   y1+r, x2,   y2-r], fill=fill)
    for cx, cy in [(x1,y1),(x2-2*r,y1),(x1,y2-2*r),(x2-2*r,y2-2*r)]:
        draw.ellipse([cx, cy, cx+2*r, cy+2*r], fill=fill)
    if outline and ow:
        draw.rounded_rectangle([x1,y1,x2,y2], radius=r,
                               outline=outline, width=ow)

# ── ID CARD ────────────────────────────────────────────────────────────────────
def generate_id_card_image(student):
    """
    Clean professional ID card – 1050 × 660 px
    LEFT  : navy panel  – logo + school name + photo + QR + status
    RIGHT : white panel – student details in a neat grid
    """
    W, H = 1050, 660
    LW   = 280          # left panel width
    PAD  = 20           # general padding
    INNER_R = 16        # inner white card radius

    img  = Image.new('RGB', (W, H), NAVY_D)
    draw = ImageDraw.Draw(img)

    # ── full background ──────────────────────────────────────────────────────
    draw.rectangle([0, 0, W, H], fill=NAVY_D)

    # ── red + gold top bar ───────────────────────────────────────────────────
    draw.rectangle([0,  0, W,  8], fill=RED)
    draw.rectangle([0,  8, W, 18], fill=GOLD)

    # ── red + gold bottom bar ────────────────────────────────────────────────
    draw.rectangle([0, H- 8, W, H  ], fill=RED)
    draw.rectangle([0, H-18, W, H-8], fill=GOLD)

    # ── LEFT PANEL ───────────────────────────────────────────────────────────
    draw.rectangle([0, 18, LW, H-18], fill=NAVY_D)

    # — Logo —
    LOGO_SZ = 110
    lx = (LW - LOGO_SZ) // 2
    ly = 30
    logo_path = os.path.join(current_app.root_path, 'static', 'images', 'logo.jpg')
    if os.path.exists(logo_path):
        try:
            logo = Image.open(logo_path).convert('RGBA').resize(
                (LOGO_SZ, LOGO_SZ), Image.LANCZOS)
            mask = Image.new('L', (LOGO_SZ, LOGO_SZ), 0)
            ImageDraw.Draw(mask).ellipse([0,0,LOGO_SZ,LOGO_SZ], fill=255)
            circ = Image.new('RGBA', (LOGO_SZ, LOGO_SZ), (0,0,0,0))
            circ.paste(logo, mask=mask)
            # gold ring
            draw.ellipse([lx-4, ly-4, lx+LOGO_SZ+4, ly+LOGO_SZ+4],
                         outline=GOLD, width=3)
            img.paste(circ, (lx, ly), circ)
        except: pass

    # — School text —
    cx = LW // 2
    ty = ly + LOGO_SZ + 12
    for line, col, sz, bold in [
        ("THE FEDERAL",           GOLD,   11, True),
        ("POLYTECHNIC",           GOLD,   11, True),
        ("NASARAWA",              WHITE,  12, True),
    ]:
        draw.text((cx, ty), line, font=fnt(sz, bold), fill=col, anchor='mm')
        ty += 16
    draw.line([(24, ty+2), (LW-24, ty+2)], fill=GOLD, width=1)
    ty += 10
    draw.text((cx, ty), "STUDENT IDENTITY CARD",
              font=fnt(8, False), fill=MGREY, anchor='mm')
    ty += 16

    # — Photo —
    PH_W, PH_H = 200, 210
    px = (LW - PH_W) // 2
    py = ty + 6
    # gold frame
    draw.rectangle([px-3, py-3, px+PH_W+3, py+PH_H+3], fill=GOLD)

    photo_ok = False
    if student.photo_filename:
        ph_path = os.path.join(current_app.config['UPLOAD_FOLDER'],
                               student.photo_filename)
        if os.path.exists(ph_path):
            try:
                ph = Image.open(ph_path).convert('RGB')
                # smart crop to square centre
                pw, phh = ph.size
                side = min(pw, phh)
                left = (pw  - side) // 2
                top  = (phh - side) // 2
                ph   = ph.crop((left, top, left+side, top+side))
                ph   = ph.resize((PH_W, PH_H), Image.LANCZOS)
                img.paste(ph, (px, py))
                photo_ok = True
            except: pass

    if not photo_ok:
        # nice placeholder
        ph = Image.new('RGB', (PH_W, PH_H), NAVY_L)
        pd = ImageDraw.Draw(ph)
        pd.ellipse([PH_W//2-45, 18, PH_W//2+45, 108], fill=(80,105,190))
        pd.ellipse([PH_W//2-75, 108, PH_W//2+75, PH_H+30], fill=(80,105,190))
        pd.text((PH_W//2, PH_H//2+30), "NO PHOTO",
                font=fnt(11, True), fill=MGREY, anchor='mm')
        img.paste(ph, (px, py))

    qr_top = py + PH_H + 14

    # — QR Code —
    QR_SZ = 120
    qx = (LW - QR_SZ) // 2
    if student.qr_filename:
        qr_path = os.path.join(current_app.config['QR_FOLDER'],
                               student.qr_filename)
        if os.path.exists(qr_path):
            try:
                qr_i = Image.open(qr_path).convert('RGB').resize(
                    (QR_SZ, QR_SZ), Image.LANCZOS)
                bg = Image.new('RGB', (QR_SZ+8, QR_SZ+8), WHITE)
                bg.paste(qr_i, (4,4))
                img.paste(bg, (qx-4, qr_top))
            except: pass

    draw.text((cx, qr_top + QR_SZ + 12),
              "SCAN TO VERIFY", font=fnt(9, False), fill=MGREY, anchor='mm')

    # — Status badge —
    status     = (student.card_status or 'active').upper()
    badge_fill = (46,125,50) if status == 'ACTIVE' else RED
    bw, bh = 150, 28
    bx = (LW - bw) // 2
    by = qr_top + QR_SZ + 26
    rr(draw, bx, by, bx+bw, by+bh, 8, badge_fill)
    draw.text((cx, by + bh//2),
              f"● {status}", font=fnt(12, True), fill=WHITE, anchor='mm')

    # ── RIGHT PANEL (white rounded card) ─────────────────────────────────────
    RP_X1 = LW + 12
    RP_Y1 = 18
    RP_X2 = W  - 12
    RP_Y2 = H  - 18
    rr(draw, RP_X1, RP_Y1, RP_X2, RP_Y2, INNER_R, WHITE)

    # content margins inside white card
    CX = RP_X1 + PAD + 4          # content left
    CY = RP_Y1 + PAD              # content top
    CR = RP_X2 - PAD - 4          # content right
    CW = CR - CX                  # content width

    # — Student name —
    name_f  = fnt(26, True)
    name    = student.full_name.upper()
    lines   = wrap(draw, name, name_f, CW)
    ny = CY + 6
    for line in lines:
        draw.text((CX, ny), line, font=name_f, fill=NAVY_D)
        ny += 34

    # gold divider
    draw.rectangle([CX, ny+2, CR, ny+5], fill=GOLD)
    ny += 18

    # — Info grid (2 columns) —
    lbl_f   = fnt(10, False)
    val_f   = fnt(15, True)
    row_h   = 54
    col_w   = CW // 2 - 8

    fields = [
        ("MATRIC NUMBER",    student.matric_number),
        ("LEVEL",            student.level),
        ("DEPARTMENT",       student.department),
        ("ACADEMIC SESSION", student.academic_session),
        ("SCHOOL",           student.school),
        ("VALID UNTIL",      student.card_expiry.strftime('%B %Y')
                             if student.card_expiry else "—"),
    ]
    if student.gender:
        fields.append(("GENDER", student.gender))

    for i, (label, value) in enumerate(fields):
        col   = i % 2
        row   = i // 2
        fx    = CX + col * (col_w + 16)
        fy    = ny + row * row_h

        draw.text((fx, fy),      label, font=lbl_f, fill=MID)
        # truncate long values
        val_disp = value
        while tw(draw, val_disp, val_f) > col_w and len(val_disp) > 4:
            val_disp = val_disp[:-2]
        draw.text((fx, fy + 14),  val_disp, font=val_f, fill=DARK)
        draw.line([(fx, fy+36), (fx+col_w, fy+36)], fill=LGREY, width=1)

    # — Watermark logo in empty space of right panel —
    logo_path2 = os.path.join(current_app.root_path, 'static', 'images', 'logo.jpg')
    if os.path.exists(logo_path2):
        try:
            wm = Image.open(logo_path2).convert('RGBA')
            wm_sz = 160
            wm = wm.resize((wm_sz, wm_sz), Image.LANCZOS)
            # make it semi-transparent
            r2,g2,b2,a2 = wm.split()
            a2 = a2.point(lambda x: int(x * 0.08))
            wm.putalpha(a2)
            wm_x = RP_X2 - wm_sz - 30
            wm_y = RP_Y1 + (RP_Y2 - RP_Y1) // 2 - wm_sz // 2
            img.paste(wm, (wm_x, wm_y), wm)
        except: pass

    # — Navy footer strip inside white card —
    footer_y = RP_Y2 - 36
    rr(draw, RP_X1, footer_y, RP_X2, RP_Y2, INNER_R, NAVY)
    # cover top-left/right round corners of footer by filling rectangle top
    draw.rectangle([RP_X1, footer_y, RP_X2, footer_y+INNER_R], fill=NAVY)
    draw.text(((RP_X1+RP_X2)//2, footer_y+18),
              "Federal Polytechnic Nasarawa  ●  Learning, Technology & Service",
              font=fnt(10, False), fill=GOLD_L, anchor='mm')

    # ── Save ─────────────────────────────────────────────────────────────────
    fn = f"idcard_{student.matric_number.replace('/', '_')}.png"
    fp = os.path.join(current_app.config['IDCARD_FOLDER'], fn)
    img.save(fp, 'PNG', dpi=(150,150))
    return fn


# ── PDF ────────────────────────────────────────────────────────────────────────
def generate_id_card_pdf(student):
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas as rl_canvas

    png_fn   = generate_id_card_image(student)
    png_path = os.path.join(current_app.config['IDCARD_FOLDER'], png_fn)

    card_w, card_h = 85.6*mm, 53.98*mm
    pdf_fn   = png_fn.replace('.png', '.pdf')
    pdf_path = os.path.join(current_app.config['IDCARD_FOLDER'], pdf_fn)

    c = rl_canvas.Canvas(pdf_path, pagesize=(card_w, card_h))
    if os.path.exists(png_path):
        c.drawImage(png_path, 0, 0, width=card_w, height=card_h,
                    preserveAspectRatio=False)
    c.save()
    return pdf_fn


def image_to_base64(filepath):
    with open(filepath, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')
