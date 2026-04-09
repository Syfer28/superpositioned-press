#!/usr/bin/env python3
"""
The Superpositioned Press — A Quantum Newspaper Management Game
Run: python3 superpositioned_press.py
Keys: 1=Investigate  2=Cross-Reference  3=Publish  4=Skip Turn  ESC=Deselect
"""

import pygame
import sys
import math
import random
import os
from dataclasses import dataclass
from typing import Optional, List, Tuple
from PIL import Image, ImageDraw, ImageFont as _PILImageFont

pygame.init()

# ── Window ────────────────────────────────────────────────────────────────────
SW, SH = 1280, 800
screen = pygame.display.set_mode((SW, SH))
pygame.display.set_caption("The Superpositioned Press")
clock = pygame.time.Clock()
TICK = 0

# ── Game Constants ────────────────────────────────────────────────────────────
DAYS           = 7
TURNS_PER_DAY  = 10
MAX_JOURNALISTS = 5
TRUST_START    = 70
TRUST_WIN      = 60
TRUST_MAX      = 100
MAX_STORIES    = 8

# ── Palette ───────────────────────────────────────────────────────────────────
BG       = (15,  13,  10)
PANEL    = (26,  22,  16)
PANEL_HL = (40,  34,  24)
BORDER   = (62,  54,  36)
ACCENT   = (212, 182,  72)
TEXT     = (224, 216, 192)
DIM      = (108,  98,  76)
TRUE_C   = ( 76, 200, 112)
FAKE_C   = (210,  72,  62)
WARN_C   = (210, 148,  52)
QUANTUM  = (150, 108, 230)
SEL_BG   = ( 48,  42,  28)
BTN_DEF  = ( 44,  38,  26)
BTN_DIS  = ( 24,  20,  14)
WHITE    = (255, 255, 255)

# ── Fonts (PIL/Pillow — avoids pygame.font circular-import bug on Python 3.14) ─
_FONT_PATHS = [
    ('/System/Library/Fonts/Supplemental/Courier New Bold.ttf',
     '/System/Library/Fonts/Supplemental/Courier New.ttf'),
    ('/System/Library/Fonts/Monaco.ttf',
     '/System/Library/Fonts/Monaco.ttf'),
    ('/System/Library/Fonts/Menlo.ttc',
     '/System/Library/Fonts/Menlo.ttc'),
    ('/System/Library/Fonts/Courier.ttc',
     '/System/Library/Fonts/Courier.ttc'),
]
_TEXT_CACHE: dict = {}

class _Font:
    _id_counter = 0

    def __init__(self, pil_font, font_id: int):
        self._pil = pil_font
        self._id  = font_id
        # Measure a typical line height once
        dummy = Image.new('RGBA', (1, 1))
        bbox  = ImageDraw.Draw(dummy).textbbox((0, 0), 'Xg|', font=pil_font)
        self._h = max(8, bbox[3] - bbox[1] + 4)

    def render(self, text: str, antialias: bool, color) -> pygame.Surface:
        text = str(text)
        key  = (self._id, text, color[:3] if len(color) >= 3 else color)
        if key in _TEXT_CACHE:
            return _TEXT_CACHE[key]

        if not text:
            surf = pygame.Surface((1, self._h), pygame.SRCALPHA)
            _TEXT_CACHE[key] = surf
            return surf

        dummy = Image.new('RGBA', (1, 1))
        bbox  = ImageDraw.Draw(dummy).textbbox((0, 0), text, font=self._pil)
        w = max(1, bbox[2] - bbox[0] + 4)
        h = max(1, bbox[3] - bbox[1] + 4)

        img  = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.text((-bbox[0] + 2, -bbox[1] + 2), text, font=self._pil,
                  fill=(int(color[0]), int(color[1]), int(color[2]), 255))

        surf = pygame.image.fromstring(img.tobytes(), img.size, 'RGBA').convert_alpha()

        if len(_TEXT_CACHE) > 800:           # simple eviction
            for k in list(_TEXT_CACHE)[:400]:
                del _TEXT_CACHE[k]
        _TEXT_CACHE[key] = surf
        return surf


def mkfont(size: int, bold: bool = False) -> _Font:
    _Font._id_counter += 1
    fid = _Font._id_counter
    for bold_path, reg_path in _FONT_PATHS:
        path = bold_path if bold else reg_path
        if os.path.exists(path):
            try:
                return _Font(_PILImageFont.truetype(path, size), fid)
            except Exception:
                pass
    # Final fallback: PIL built-in bitmap font
    try:
        return _Font(_PILImageFont.load_default(size=size), fid)
    except TypeError:
        return _Font(_PILImageFont.load_default(), fid)

FT = mkfont(28, True)
FH = mkfont(20, True)
FM = mkfont(16)
FB = mkfont(14)
FS = mkfont(12)

# ── Story Content ─────────────────────────────────────────────────────────────
HEADLINES = {
    "Politics": [
        "Senator caught in midnight document leak",
        "Mayor's aide linked to offshore accounts",
        "Governor signs secret budget amendment",
        "Whistleblower alleges election interference",
        "Ministry denies secret surveillance program",
        "Cabinet minister resigns amid bribery claims",
        "PM's office accused of data manipulation",
        "Opposition files emergency injunction",
    ],
    "Science": [
        "Lab claims cold fusion breakthrough — again",
        "Satellite data suggests hidden continent",
        "Vaccine trial shows unexpected side effects",
        "AI system passes consciousness test",
        "Ancient DNA rewrites human migration story",
        "Physicists detect anomaly in standard model",
        "Biotech firm accused of hiding trial failures",
        "Space agency covers up anomalous signal",
    ],
    "Economy": [
        "Crypto exchange freezes all withdrawals",
        "Housing bubble warnings ignored by regulators",
        "Factory closures spike in industrial belt",
        "Central bank leak hints at rate reversal",
        "Tech giant acquires rival in secret merger",
        "Pension fund collapse leaves thousands exposed",
        "Insider trading ring tied to finance ministry",
        "Currency manipulation probe quietly expands",
    ],
    "Crime": [
        "Evidence tampering alleged at precinct 7",
        "Organized ring hacks city water system",
        "Heist at museum: artifacts missing for weeks",
        "Witness recants testimony in murder trial",
        "Hacker collective exposes police databases",
        "Cartel connections found in city council",
        "Drug network extends into school system",
        "Arson spree linked to property developer",
    ],
    "Culture": [
        "Famous artist's new work contains coded message",
        "Festival permit revoked hours before opening",
        "Celebrity memoir contains fabricated events",
        "Historic building demolished without notice",
        "Underground movement calls for media blackout",
        "Award-winning film linked to propaganda ring",
        "Renowned journalist fabricated key interviews",
        "Cultural institute fund misappropriation found",
    ],
}

CAT_COLORS = {
    "Politics": (212, 148,  72),
    "Science":  (100, 180, 220),
    "Economy":  (148, 200, 100),
    "Crime":    (200, 100, 100),
    "Culture":  (180, 130, 220),
}


# ── Helpers ───────────────────────────────────────────────────────────────────
def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def blit(surf, text, pos, font=None, color=TEXT):
    font = font or FB
    s = font.render(str(text), True, color)
    surf.blit(s, pos)
    return s.get_rect(topleft=pos)


def draw_panel(surf, rect, bg=PANEL, border=BORDER, r=3):
    pygame.draw.rect(surf, bg, rect, border_radius=r)
    pygame.draw.rect(surf, border, rect, 1, border_radius=r)


# ── Quantum Story ─────────────────────────────────────────────────────────────
@dataclass
class Story:
    sid:           int
    headline:      str
    category:      str
    theta:         float        # 0 = pure Truth, π = pure Fake
    source_count:  int
    source_phases: List[float]
    turns_left:    int
    importance:    int          # 1-3
    investigated:  int = 0
    cross_reffed:  int = 0

    @property
    def truth_prob(self) -> float:
        return math.cos(self.theta / 2) ** 2

    @property
    def prob_pct(self) -> int:
        return int(self.truth_prob * 100)

    @property
    def alignment(self) -> str:
        """Compute source phase alignment for interference prediction."""
        if self.source_count < 2:
            return "single"
        diffs = []
        for i in range(len(self.source_phases) - 1):
            d = abs(self.source_phases[i] - self.source_phases[i + 1])
            diffs.append(min(d, 2 * math.pi - d))
        avg = sum(diffs) / len(diffs)
        if avg < math.pi / 3:
            return "aligned"
        elif avg > 2 * math.pi / 3:
            return "opposing"
        return "mixed"

    def do_investigate(self) -> Tuple[str, str]:
        """Weak measurement: nudge state toward Truth without collapse."""
        shift = clamp(random.gauss(0.22, 0.08), 0.05, 0.45)
        self.theta = clamp(self.theta - shift, 0.05, math.pi - 0.05)
        self.investigated += 1
        return f"Weak measurement complete. Truth probability nudged +{int(shift*35)}%.", "system"

    def do_cross_reference(self) -> Tuple[str, str]:
        """Apply quantum interference from multiple sources."""
        if self.source_count < 2:
            return "Only one source — interference impossible.", "warn"
        al = self.alignment
        if al == "aligned":
            shift = clamp(random.gauss(0.55, 0.12), 0.3, 0.9)
            self.theta = clamp(self.theta - shift, 0.05, math.pi - 0.05)
            self.cross_reffed += 1
            return "CONSTRUCTIVE interference! Sources reinforce — truth probability surges!", "truth"
        elif al == "opposing":
            self.theta = self.theta + (math.pi / 2 - self.theta) * 0.5
            self.cross_reffed += 1
            return "DESTRUCTIVE interference! Sources cancel — wave function destabilised!", "fake"
        else:
            shift = clamp(random.gauss(0.18, 0.08), 0.05, 0.35)
            self.theta = clamp(self.theta - shift, 0.05, math.pi - 0.05)
            self.cross_reffed += 1
            return "Partial interference: modest truth improvement.", "warn"

    def collapse(self) -> bool:
        """Wave-function collapse: measure the story."""
        return random.random() < self.truth_prob


# ── Game State ────────────────────────────────────────────────────────────────
class GameState:
    def __init__(self):
        self.day         = 1
        self.turn        = 1
        self.trust       = TRUST_START
        self.journalists = MAX_JOURNALISTS
        self.stories: List[Story]         = []
        self.log:     List[Tuple[str,str]] = []
        self.published   = 0
        self.truths      = 0
        self.fakes       = 0
        self.selected: Optional[Story]    = None
        self._nid        = 0
        self.game_over   = False
        self.won         = False
        self.flash_msg   = ""
        self.flash_timer = 0

        for _ in range(3):
            self.spawn_story()
        self.add_log("Welcome, Head Observer. Reality awaits your measurement.", "system")
        self.add_log("Investigate, cross-reference, and publish stories wisely.", "system")

    # ── Logging ──────────────────────────────────────────────────────────────
    def add_log(self, msg: str, kind: str = "system"):
        self.log.insert(0, (msg, kind))
        if len(self.log) > 40:
            self.log.pop()

    def flash(self, msg: str):
        self.flash_msg   = msg
        self.flash_timer = 150

    # ── Story spawning ────────────────────────────────────────────────────────
    def spawn_story(self):
        if len(self.stories) >= MAX_STORIES:
            return
        cat  = random.choice(list(HEADLINES.keys()))
        used = {s.headline for s in self.stories}
        pool = [h for h in HEADLINES[cat] if h not in used]
        if not pool:
            return
        headline = random.choice(pool)
        theta    = random.uniform(0.7, 2.5)
        n_src    = random.randint(1, 4)
        base_ph  = random.uniform(0, 2 * math.pi)
        phases   = []
        for _ in range(n_src):
            if random.random() < 0.55:
                phases.append(base_ph + random.uniform(-0.6, 0.6))
            else:
                phases.append(random.uniform(0, 2 * math.pi))
        s = Story(
            sid=self._nid, headline=headline, category=cat,
            theta=theta, source_count=n_src, source_phases=phases,
            turns_left=random.randint(5, 9),
            importance=random.randint(1, 3),
        )
        self._nid += 1
        self.stories.append(s)
        self.add_log(f'INCOMING: "{headline[:50]}"', "new")

    # ── Turn ──────────────────────────────────────────────────────────────────
    def advance_turn(self):
        for s in list(self.stories):
            s.turns_left -= 1
            if s.turns_left <= 0:
                self.stories.remove(s)
                if self.selected is s:
                    self.selected = None
                penalty = random.choice([-3, -4, -5])
                self.trust = clamp(self.trust + penalty, 0, TRUST_MAX)
                self.add_log(f'EXPIRED: "{s.headline[:42]}" — Trust {penalty}', "warn")

        self.turn += 1
        if self.turn > TURNS_PER_DAY:
            self.turn = 1
            self.day += 1
            self.journalists = MAX_JOURNALISTS
            self.add_log(f"━━ Day {self.day}/{DAYS} — Journalist pool restored ({MAX_JOURNALISTS} units). ━━", "system")

        if random.random() < 0.55 and len(self.stories) < MAX_STORIES:
            self.spawn_story()

        if self.trust <= 0:
            self.trust = 0
            self.game_over = True
        elif self.day > DAYS:
            self.game_over = True
            self.won = self.trust >= TRUST_WIN

    # ── Actions ───────────────────────────────────────────────────────────────
    def action_investigate(self) -> bool:
        if not self.selected:
            self.flash("Select a story first!")
            return False
        if self.journalists < 1:
            self.flash("No journalist units available!")
            return False
        msg, kind = self.selected.do_investigate()
        self.journalists -= 1
        self.add_log(f'"{self.selected.headline[:35]}..." — {msg}', kind)
        self.advance_turn()
        return True

    def action_cross_reference(self) -> bool:
        if not self.selected:
            self.flash("Select a story first!")
            return False
        if self.journalists < 2:
            self.flash("Need at least 2 journalist units!")
            return False
        if self.selected.source_count < 2:
            self.flash("Story has only 1 source — can't cross-reference!")
            return False
        msg, kind = self.selected.do_cross_reference()
        self.journalists -= 2
        self.add_log(f'"{self.selected.headline[:35]}..." — {msg}', kind)
        self.advance_turn()
        return True

    def action_publish(self) -> bool:
        if not self.selected:
            self.flash("Select a story first!")
            return False
        story  = self.selected
        result = story.collapse()
        self.stories.remove(story)
        self.selected = None
        if result:
            gain = random.randint(8, 15) * story.importance
            self.trust = clamp(self.trust + gain, 0, TRUST_MAX)
            self.truths += 1
            self.add_log(f'PUBLISHED → TRUTH: "{story.headline[:42]}" +{gain} trust', "truth")
        else:
            loss = random.randint(10, 20) * story.importance
            self.trust = clamp(self.trust - loss, 0, TRUST_MAX)
            self.fakes += 1
            self.add_log(f'PUBLISHED → FAKE:  "{story.headline[:42]}" −{loss} trust', "fake")
        self.published += 1
        self.advance_turn()
        return True

    def action_skip(self):
        self.add_log("Turn advanced — no action taken.", "system")
        self.advance_turn()


# ── Layout Rects ─────────────────────────────────────────────────────────────
HEADER_H  = 68
LOG_H     = 155
FEED_W    = 370
CONTENT_Y = HEADER_H
CONTENT_H = SH - HEADER_H - LOG_H

R_HEADER = pygame.Rect(0, 0, SW, HEADER_H)
R_FEED   = pygame.Rect(0, CONTENT_Y, FEED_W, CONTENT_H)
R_DETAIL = pygame.Rect(FEED_W + 5, CONTENT_Y, SW - FEED_W - 5, CONTENT_H)
R_LOG    = pygame.Rect(0, SH - LOG_H, SW, LOG_H)

# Module-level caches updated each frame
STORY_RECTS:  dict = {}
ACTION_RECTS: dict = {}


# ── Quantum Bar ───────────────────────────────────────────────────────────────
def draw_quantum_bar(surf, rect, theta: float, t: int):
    x, y, w, h = rect
    p = math.cos(theta / 2) ** 2
    draw_panel(surf, rect, (18, 15, 11), BORDER)

    # Gradient fill
    bar_w = max(0, int((w - 2) * p))
    if bar_w > 0:
        r = int(FAKE_C[0] * (1 - p) + TRUE_C[0] * p)
        g = int(FAKE_C[1] * (1 - p) + TRUE_C[1] * p)
        b = int(FAKE_C[2] * (1 - p) + TRUE_C[2] * p)
        pygame.draw.rect(surf, (r, g, b), (x + 1, y + 1, bar_w, h - 2))

    # Wave overlay (superposition animation)
    amplitude = 2 + int(5 * math.sin(theta))
    pts = []
    for px in range(x + 1, x + w - 1, 2):
        phase = (px - x) / w * 4 * math.pi - t * 0.07
        pts.append((px, y + h // 2 + int(amplitude * math.sin(phase))))
    if len(pts) > 1:
        wave_r = min(255, int(FAKE_C[0]*(1-p) + TRUE_C[0]*p) + 50)
        wave_g = min(255, int(FAKE_C[1]*(1-p) + TRUE_C[1]*p) + 50)
        wave_b = min(255, int(FAKE_C[2]*(1-p) + TRUE_C[2]*p) + 50)
        pygame.draw.lines(surf, (wave_r, wave_g, wave_b), False, pts, 1)

    # Centre dashes
    for px in range(x + 3, x + w - 3, 6):
        pygame.draw.line(surf, DIM, (px, y + h // 2), (px + 3, y + h // 2), 1)

    # Labels
    blit(surf, "TRUTH", (x + 4, y + 2), FS, TRUE_C)
    blit(surf, "FAKE",  (x + w - 32, y + 2), FS, FAKE_C)
    blit(surf, f"{int(p * 100)}%", (x + bar_w - 16, y + h - 13), FS, WHITE)

    # Pointer
    mx = clamp(x + bar_w, x + 4, x + w - 4)
    pygame.draw.polygon(surf, ACCENT, [(mx - 5, y), (mx + 5, y), (mx, y + 8)])


# ── Source Phase Diagram ──────────────────────────────────────────────────────
def draw_source_phases(surf, x: int, y: int, s: Story):
    cx, cy, r = x + 40, y + 38, 30
    pygame.draw.circle(surf, PANEL_HL, (cx, cy), r)
    pygame.draw.circle(surf, BORDER,   (cx, cy), r, 1)
    pygame.draw.line(surf, (40, 35, 25), (cx - r, cy), (cx + r, cy), 1)
    pygame.draw.line(surf, (40, 35, 25), (cx, cy - r), (cx, cy + r), 1)
    cat_c = CAT_COLORS.get(s.category, QUANTUM)
    for ph in s.source_phases:
        vx = int(cx + r * 0.85 * math.cos(ph))
        vy = int(cy - r * 0.85 * math.sin(ph))
        pygame.draw.line(surf, cat_c, (cx, cy), (vx, vy), 2)
        pygame.draw.circle(surf, cat_c, (vx, vy), 3)
    blit(surf, "Phases", (cx - 18, y + 76), FS, DIM)

    # Alignment description
    ax, ay = x + 88, y + 10
    al = s.alignment
    if al == "aligned":
        blit(surf, "CONSTRUCTIVE INTERFERENCE", (ax, ay),      FB, TRUE_C)
        blit(surf, "Sources reinforce each other.",             (ax, ay+16), FS, DIM)
        blit(surf, "Cross-reference is recommended!",          (ax, ay+30), FS, TRUE_C)
    elif al == "opposing":
        blit(surf, "DESTRUCTIVE INTERFERENCE",  (ax, ay),      FB, FAKE_C)
        blit(surf, "Sources contradict and cancel.",           (ax, ay+16), FS, DIM)
        blit(surf, "Cross-reference will destabilise state!",  (ax, ay+30), FS, FAKE_C)
    elif al == "single":
        blit(surf, "SINGLE SOURCE",             (ax, ay),      FB, DIM)
        blit(surf, "Interference not possible.", (ax, ay+16),  FS, DIM)
        blit(surf, "Use Investigate instead.",   (ax, ay+30),  FS, WARN_C)
    else:
        blit(surf, "PARTIAL INTERFERENCE",      (ax, ay),      FB, WARN_C)
        blit(surf, "Sources partially align.",  (ax, ay+16),   FS, DIM)
        blit(surf, "Cross-reference may help.", (ax, ay+30),   FS, WARN_C)


# ── Header ────────────────────────────────────────────────────────────────────
def draw_header(surf, g: GameState, t: int):
    draw_panel(surf, R_HEADER, (20, 17, 12), BORDER)

    blit(surf, "THE SUPERPOSITIONED PRESS", (12, 9),  FT, ACCENT)
    blit(surf, "HEAD OBSERVER'S CONSOLE",   (12, 42), FS, DIM)

    # Day / Turn
    blit(surf, f"Day {g.day} / {DAYS}    Turn {g.turn} / {TURNS_PER_DAY}",
         (490, 9), FH, TEXT)

    # Trust bar
    bx, by, bw, bh = 490, 37, 210, 20
    pygame.draw.rect(surf, (28, 24, 18), (bx, by, bw, bh))
    tw  = int(bw * g.trust / TRUST_MAX)
    tc  = TRUE_C if g.trust > 50 else (WARN_C if g.trust > 25 else FAKE_C)
    if tw > 0:
        pygame.draw.rect(surf, tc, (bx, by, tw, bh))
    pygame.draw.rect(surf, BORDER, (bx, by, bw, bh), 1)
    blit(surf, f"TRUST: {g.trust}%", (bx + bw + 6, by + 2), FS, tc)

    # Journalist dots
    jx = 830
    blit(surf, "JOURNALISTS:", (jx, 9), FB, DIM)
    for i in range(MAX_JOURNALISTS):
        cx2 = jx + 108 + i * 22
        pygame.draw.circle(surf, ACCENT if i < g.journalists else (50, 44, 30), (cx2, 17), 7)
        if i >= g.journalists:
            pygame.draw.circle(surf, BORDER, (cx2, 17), 7, 1)
    blit(surf, f"{g.journalists}/{MAX_JOURNALISTS} available", (jx, 38), FS, DIM)

    # Stats
    blit(surf, f"Published: {g.published}",  (1070,  7), FS, DIM)
    blit(surf, f"  Truths:  {g.truths}",     (1070, 21), FS, TRUE_C)
    blit(surf, f"  Fakes:   {g.fakes}",      (1070, 35), FS, FAKE_C)

    # Flash
    if g.flash_timer > 0:
        ms = FH.render(g.flash_msg, True, WARN_C)
        surf.blit(ms, (SW // 2 - ms.get_width() // 2, SH // 2 - 18))
        g.flash_timer -= 1


# ── Story Feed ────────────────────────────────────────────────────────────────
def draw_feed(surf, g: GameState, t: int, mpos: tuple):
    global STORY_RECTS
    STORY_RECTS = {}
    draw_panel(surf, R_FEED, PANEL, BORDER)

    x, y = R_FEED.x + 4, R_FEED.y + 4
    w    = R_FEED.width - 8

    blit(surf, "INCOMING STORIES", (x + 4, y + 4), FH, ACCENT)
    blit(surf, f"{len(g.stories)}/{MAX_STORIES}", (x + w - 42, y + 6), FS, DIM)
    y += 28
    pygame.draw.line(surf, BORDER, (x, y), (x + w, y), 1)
    y += 4

    for s in g.stories:
        sh = 65
        r  = pygame.Rect(x, y, w, sh)
        STORY_RECTS[s.sid] = r

        is_sel = g.selected and g.selected.sid == s.sid
        is_hov = r.collidepoint(mpos)
        bg     = SEL_BG if is_sel else (PANEL_HL if is_hov else PANEL)
        draw_panel(surf, r, bg, ACCENT if is_sel else (40, 35, 24))

        cat_c = CAT_COLORS.get(s.category, DIM)
        blit(surf, s.category[:3].upper(), (x + 4,  y + 4),  FS, cat_c)
        blit(surf, "★" * s.importance + "☆" * (3 - s.importance),
             (x + 46, y + 4), FS, WARN_C)
        tl_c = FAKE_C if s.turns_left <= 2 else (WARN_C if s.turns_left <= 4 else DIM)
        blit(surf, f"{s.turns_left}t", (x + w - 26, y + 4), FS, tl_c)

        hl = s.headline if len(s.headline) <= 40 else s.headline[:37] + "..."
        blit(surf, hl, (x + 4, y + 18), FB, TEXT)

        # Mini probability bar
        pbx, pby, pbw, pbh = x + 4, y + 38, w - 8, 14
        pygame.draw.rect(surf, (18, 15, 11), (pbx, pby, pbw, pbh))
        pw = int(pbw * s.truth_prob)
        pr = int(FAKE_C[0]*(1-s.truth_prob) + TRUE_C[0]*s.truth_prob)
        pg = int(FAKE_C[1]*(1-s.truth_prob) + TRUE_C[1]*s.truth_prob)
        pb = int(FAKE_C[2]*(1-s.truth_prob) + TRUE_C[2]*s.truth_prob)
        if pw > 0:
            pygame.draw.rect(surf, (pr, pg, pb), (pbx, pby, pw, pbh))
        pygame.draw.rect(surf, BORDER, (pbx, pby, pbw, pbh), 1)

        info = f"T:{s.prob_pct}%"
        if s.investigated:  info += f"  inv×{s.investigated}"
        if s.cross_reffed:  info += f"  xrf×{s.cross_reffed}"
        blit(surf, info, (pbx + 2, pby + 1), FS, TEXT)

        y += sh + 3
        if y + sh > R_FEED.bottom - 4:
            break

    # "No stories" hint
    if not g.stories:
        blit(surf, "No active stories.", (x + 20, R_FEED.centery - 10), FM, DIM)
        blit(surf, "Wait for the next turn.", (x + 10, R_FEED.centery + 12), FS, DIM)


# ── Story Detail + Actions ────────────────────────────────────────────────────
def draw_detail(surf, g: GameState, t: int):
    global ACTION_RECTS
    draw_panel(surf, R_DETAIL, PANEL, BORDER)

    x, y = R_DETAIL.x + 8, R_DETAIL.y + 8
    w    = R_DETAIL.width - 16

    # ── Action buttons (always at bottom) ────────────────────────────────────
    ACTION_RECTS = {}
    act_y   = R_DETAIL.bottom - 138
    pygame.draw.line(surf, BORDER, (x, act_y), (x + w, act_y), 1)
    act_y  += 5
    blit(surf, "ACTIONS", (x, act_y), FH, ACCENT)
    blit(surf, f"({g.journalists} journalist unit{'s' if g.journalists != 1 else ''} available)",
         (x + 88, act_y + 3), FS, DIM)
    act_y += 26

    s    = g.selected
    btnw = (w - 9) // 4
    btnh = 52
    buttons = [
        dict(key="investigate", label="[1] INVESTIGATE",
             sub="Cost: 1 journalist", sub2="Weak measurement",
             color=TRUE_C,
             ok=s is not None and g.journalists >= 1),
        dict(key="cross_ref",   label="[2] CROSS-REF",
             sub="Cost: 2 journalists", sub2="Apply interference",
             color=QUANTUM,
             ok=s is not None and g.journalists >= 2 and s.source_count >= 2),
        dict(key="publish",     label="[3] PUBLISH",
             sub="Cost: 0 journalists", sub2="⚠ Wave collapses!",
             color=WARN_C,
             ok=s is not None),
        dict(key="skip",        label="[4] SKIP TURN",
             sub="Advance time only", sub2="No action taken",
             color=DIM, ok=True),
    ]
    for i, btn in enumerate(buttons):
        bx  = x + i * (btnw + 3)
        br  = pygame.Rect(bx, act_y, btnw, btnh)
        ACTION_RECTS[btn["key"]] = br
        ok  = btn["ok"]
        draw_panel(surf, br, BTN_DEF if ok else BTN_DIS, btn["color"] if ok else BORDER, 4)
        col = btn["color"] if ok else (48, 42, 30)
        sub = DIM if ok else (40, 36, 28)
        lbl = FB.render(btn["label"], True, col)
        surf.blit(lbl, (bx + btnw // 2 - lbl.get_width() // 2, act_y + 6))
        s1 = FS.render(btn["sub"],  True, sub)
        s2 = FS.render(btn["sub2"], True, sub)
        surf.blit(s1, (bx + btnw // 2 - s1.get_width() // 2, act_y + 24))
        surf.blit(s2, (bx + btnw // 2 - s2.get_width() // 2, act_y + 38))

    # ── If no story selected ──────────────────────────────────────────────────
    if not g.selected:
        mid_y = R_DETAIL.y + (act_y - R_DETAIL.y) // 2
        blit(surf, "← SELECT A STORY", (x + w // 2 - 90, mid_y - 16), FH, DIM)
        blit(surf, "Click a story in the feed to inspect its quantum state.",
             (x + 20, mid_y + 10), FS, DIM)
        return

    # ── Story details ─────────────────────────────────────────────────────────
    sv = g.selected
    blit(surf, "STORY ANALYSIS — QUANTUM STATE INSPECTOR", (x, y), FH, ACCENT)
    y += 24
    pygame.draw.line(surf, BORDER, (x, y), (x + w, y), 1)
    y += 6

    cat_c = CAT_COLORS.get(sv.category, DIM)
    blit(surf, f"[{sv.category.upper()}]",  (x, y),           FB, cat_c)
    blit(surf, "★" * sv.importance + "☆" * (3 - sv.importance), (x + 110, y), FB, WARN_C)
    tl_c = FAKE_C if sv.turns_left <= 2 else (WARN_C if sv.turns_left <= 4 else TEXT)
    blit(surf, f"Deadline: {sv.turns_left} turns", (x + w - 125, y), FB, tl_c)
    y += 20

    hl = f'"{sv.headline}"'
    blit(surf, hl, (x, y), FH, TEXT)
    y += 28

    # Quantum state
    blit(surf, "QUANTUM STATE", (x, y), FH, QUANTUM)
    y += 22
    alpha = math.cos(sv.theta / 2)
    beta  = math.sin(sv.theta / 2)
    blit(surf, f"|ψ⟩ = {alpha:.3f}|Truth⟩ + {beta:.3f}|Fake⟩", (x, y), FM, TEXT)
    y += 20
    blit(surf,
         f"θ = {math.degrees(sv.theta):.1f}°    "
         f"|α|² (truth) = {sv.truth_prob:.3f}    "
         f"|β|² (fake)  = {1 - sv.truth_prob:.3f}",
         (x, y), FS, DIM)
    y += 20
    draw_quantum_bar(surf, (x, y, w, 32), sv.theta, t)
    y += 42

    # Sources
    blit(surf, "SOURCES & INTERFERENCE", (x, y), FH, QUANTUM)
    y += 20
    blit(surf, f"Sources available: {sv.source_count}", (x, y), FB, TEXT)
    y += 18
    draw_source_phases(surf, x, y, sv)
    y += 92

    blit(surf,
         f"Investigated: {sv.investigated}×    Cross-referenced: {sv.cross_reffed}×",
         (x, y), FS, DIM)


# ── Log Bar ───────────────────────────────────────────────────────────────────
def draw_log(surf, g: GameState):
    draw_panel(surf, R_LOG, (18, 15, 11), BORDER)
    blit(surf, "NEWSROOM LOG", (R_LOG.x + 6, R_LOG.y + 5), FH, ACCENT)
    log_c = {"truth": TRUE_C, "fake": FAKE_C, "new": QUANTUM,
             "warn": WARN_C, "system": DIM}
    ly = R_LOG.y + 27
    for msg, kind in g.log[:8]:
        blit(surf, msg[:118], (R_LOG.x + 6, ly), FS, log_c.get(kind, DIM))
        ly += 15


# ── End Screen ────────────────────────────────────────────────────────────────
def draw_end_screen(surf, g: GameState):
    ov = pygame.Surface((SW, SH), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 175))
    surf.blit(ov, (0, 0))

    pw, ph = 560, 360
    pr = pygame.Rect(SW // 2 - pw // 2, SH // 2 - ph // 2, pw, ph)
    draw_panel(surf, pr, (28, 24, 16), ACCENT, 6)

    cx, cy = SW // 2, SH // 2

    if g.won:
        title = "REALITY SECURED"
        tcol  = TRUE_C
        sub   = "The city's truth has been preserved."
    elif g.trust <= 0:
        title = "PUBLIC TRUST COLLAPSED"
        tcol  = FAKE_C
        sub   = "The city has descended into chaos."
    else:
        title = "GAME OVER"
        tcol  = FAKE_C
        sub   = "The city lost faith in your editorial judgement."

    ts = FT.render(title, True, tcol)
    surf.blit(ts, (cx - ts.get_width() // 2, pr.y + 18))
    blit(surf, sub, (cx - 220, pr.y + 58), FM, TEXT)

    sy = pr.y + 95
    rows = [
        ("Final Trust",      f"{g.trust}%",      TRUE_C if g.trust >= TRUST_WIN else FAKE_C),
        ("Stories Published", str(g.published),   TEXT),
        ("  Truths",          str(g.truths),       TRUE_C),
        ("  Fakes",           str(g.fakes),        FAKE_C),
        ("Days Survived",    f"{min(g.day, DAYS)}/{DAYS}", TEXT),
    ]
    for label, val, col in rows:
        blit(surf, label, (cx - 160, sy), FM, DIM)
        blit(surf, val,   (cx + 80,  sy), FM, col)
        sy += 30

    blit(surf, "Press R to restart   |   ESC to quit",
         (cx - 150, pr.bottom - 38), FM, DIM)


# ── Main Menu ────────────────────────────────────────────────────────────────
def draw_menu(surf, t: int):
    surf.fill(BG)
    cx, cy = SW // 2, SH // 2

    # Animated title
    title = "THE SUPERPOSITIONED PRESS"
    ts    = FT.render(title, True, ACCENT)
    ox    = int(0)
    oy    = int(6 * math.sin(t * 0.04))
    surf.blit(ts, (cx - ts.get_width() // 2 + ox, cy - 210 + oy))

    blit(surf, "A QUANTUM NEWSPAPER MANAGEMENT GAME",
         (cx - 225, cy - 162), FH, DIM)

    # Animated quantum bar
    theta_anim = math.pi / 2 + math.sin(t * 0.025) * 1.3
    draw_quantum_bar(surf, (cx - 220, cy - 110, 440, 38), theta_anim, t)

    blit(surf, "|ψ⟩ = α|Truth⟩ + β|Fake⟩  (in superposition until published)",
         (cx - 255, cy - 60), FM, QUANTUM)

    lines = [
        "You are the Head Observer and Editor-in-Chief.",
        "News events exist in quantum superposition — both True and Fake —",
        "until your newspaper measures and publishes them.",
        "",
        "Investigate  →  Weak measurement: nudge probability toward Truth (1 journalist)",
        "Cross-Ref    →  Quantum interference: constructive or destructive (2 journalists)",
        "Publish      →  Wave-function collapse: story becomes Truth or Fake",
        "",
        f"Survive {DAYS} days. Maintain public trust above {TRUST_WIN}% to win.",
    ]
    ly = cy + 0
    for line in lines:
        blit(surf, line, (cx - 300, ly), FB, TEXT if line else DIM)
        ly += 20

    pulse = int(180 + 60 * math.sin(t * 0.08))
    col   = (pulse, pulse, int(pulse * 0.6))
    blit(surf, "Press ENTER or SPACE to begin", (cx - 155, ly + 16), FH, col)
    blit(surf, "Keys: 1=Investigate   2=Cross-Reference   3=Publish   4=Skip Turn",
         (cx - 275, ly + 44), FS, DIM)


# ── Main Loop ────────────────────────────────────────────────────────────────
def main():
    global TICK
    state = "menu"
    game: Optional[GameState] = None

    while True:
        clock.tick(60)
        TICK += 1
        mpos  = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if event.type == pygame.KEYDOWN:
                if state == "menu":
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        state = "playing"
                        game  = GameState()

                elif state == "playing" and game:
                    if event.key == pygame.K_1:
                        game.action_investigate()
                    elif event.key == pygame.K_2:
                        game.action_cross_reference()
                    elif event.key == pygame.K_3:
                        game.action_publish()
                    elif event.key == pygame.K_4:
                        game.action_skip()
                    elif event.key == pygame.K_ESCAPE:
                        game.selected = None

                elif state in ("gameover", "win"):
                    if event.key == pygame.K_r:
                        state = "playing"
                        game  = GameState()
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit(); sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if state == "playing" and game:
                    # Story selection
                    for sid, rect in STORY_RECTS.items():
                        if rect.collidepoint(mpos):
                            for s in game.stories:
                                if s.sid == sid:
                                    game.selected = s
                                    break
                    # Action buttons
                    for key, rect in ACTION_RECTS.items():
                        if rect.collidepoint(mpos):
                            if key == "investigate":
                                game.action_investigate()
                            elif key == "cross_ref":
                                game.action_cross_reference()
                            elif key == "publish":
                                game.action_publish()
                            elif key == "skip":
                                game.action_skip()

        # ── Render ──────────────────────────────────────────────────────────
        screen.fill(BG)

        if state == "menu":
            draw_menu(screen, TICK)

        elif state == "playing" and game:
            draw_header(screen, game, TICK)
            draw_feed(screen, game, TICK, mpos)
            draw_detail(screen, game, TICK)
            draw_log(screen, game)
            if game.game_over:
                state = "win" if game.won else "gameover"

        elif state in ("gameover", "win") and game:
            draw_header(screen, game, TICK)
            draw_feed(screen, game, TICK, mpos)
            draw_detail(screen, game, TICK)
            draw_log(screen, game)
            draw_end_screen(screen, game)

        pygame.display.flip()


if __name__ == "__main__":
    main()
