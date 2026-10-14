import array
import json
import math
import os
import random
import sys
import time
import pygame
from pygame.math import Vector2

# 1. Audio & Display Architecture Initialization
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
pygame.font.init()
pygame.mixer.set_num_channels(16)

CELL_SIZE = 26
CELL_COUNT = 24
WINDOW_SIZE = CELL_SIZE * CELL_COUNT

screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
pygame.display.set_caption("CYBERSNAKE: APEX // GUARDIAN PROTOCOL [GOLD MASTER]")
clock = pygame.time.Clock()
FPS = 60

# Palette
COLOR_VOID = (6, 7, 11)
COLOR_GRID_DARK = (13, 16, 24)
COLOR_GRID_LIGHT = (18, 22, 33)
COLOR_CYAN = (0, 245, 255)
COLOR_GREEN = (46, 230, 96)
COLOR_PURPLE = (175, 65, 255)
COLOR_GOLD = (255, 205, 10)
COLOR_RED = (255, 45, 85)
COLOR_WHITE = (245, 250, 255)
COLOR_METAL = (70, 80, 95)
COLOR_METAL_DARK = (30, 36, 46)

# Typography
FONT_TITLE = pygame.font.SysFont("consolas", 36, bold=True)
FONT_SUB = pygame.font.SysFont("consolas", 20, bold=True)
FONT_UI = pygame.font.SysFont("consolas", 14, bold=True)
FONT_MINI = pygame.font.SysFont("consolas", 11)


# -------------------------------------------------------------
# 2. Sound Effects & Synthesizer Utilities
# -------------------------------------------------------------
def synthesize(freq_start, freq_end, duration_sec, wave_type="sine", volume=0.25):
    sample_rate = 44100
    n_samples = int(sample_rate * duration_sec)
    buf = array.array("h")
    for i in range(n_samples):
        t = i / sample_rate
        p = i / n_samples
        f = freq_start + (freq_end - freq_start) * p
        phase = 2.0 * math.pi * f * t
        if wave_type == "square":
            sample = 1.0 if math.sin(phase) > 0 else -1.0
        elif wave_type == "saw":
            sample = 2.0 * (t * f - math.floor(0.5 + t * f))
        else:
            sample = math.sin(phase)
        sample *= (1.0 - p) ** 1.4 * volume
        # Interleave stereo channels
        val = int(sample * 32767)
        buf.append(val)
        buf.append(val)
    return pygame.mixer.Sound(buffer=buf)


SND_EAT = synthesize(520, 1050, 0.08, "sine", 0.22)
SND_SPECIAL = synthesize(300, 1200, 0.25, "saw", 0.28)
SND_MISSILE = synthesize(600, 250, 0.20, "saw", 0.18)
SND_BOSS_HIT = synthesize(180, 80, 0.35, "square", 0.45)
SND_CRASH = synthesize(220, 40, 0.45, "saw", 0.50)
SND_PORTAL = synthesize(320, 880, 0.40, "sine", 0.35)


# -------------------------------------------------------------
# 3. Dynamic Procedural Cyber-Synthwave Arpeggiator Engine
# -------------------------------------------------------------
class CyberArpeggiator:
    def __init__(self):
        self.channel_bass = pygame.mixer.Channel(14)
        self.channel_lead = pygame.mixer.Channel(15)
        self.step = 0
        self.last_tick = pygame.time.get_ticks()
        self.sound_cache = {}

        # 16-Step Arpeggio Intervals (Semitone offsets relative to root note)
        self.lead_pattern = [0, 7, 12, 15, 12, 7, 15, 19, 0, 7, 12, 14, 12, 7, 10, 7]
        self.bass_pattern = [0, -1, 0, -1, -5, -1, -5, -1, -7, -1, -7, -1, -3, -1, -2, -1]

    def note_to_freq(self, semitones_from_a4):
        return 440.0 * (2.0 ** (semitones_from_a4 / 12.0))

    def get_tone(self, freq, duration, wave_type, vol):
        key = (int(freq), round(duration, 3), wave_type, round(vol, 2))
        if key not in self.sound_cache:
            sr = 44100
            n = int(sr * duration)
            buf = array.array("h")
            for i in range(n):
                t = i / sr
                p = i / n
                phase = 2.0 * math.pi * freq * t
                if wave_type == "saw":
                    s = 2.0 * (t * freq - math.floor(0.5 + t * freq))
                elif wave_type == "square":
                    s = 1.0 if math.sin(phase) > 0 else -1.0
                else:
                    s = math.sin(phase)
                # Percussive exponential decay
                env = (1.0 - p) ** 2.0 * vol
                val = int(s * env * 32767)
                buf.append(val)
                buf.append(val)
            self.sound_cache[key] = pygame.mixer.Sound(buffer=buf)
        return self.sound_cache[key]

    def update(self, sector_num):
        # Dynamic tempo acceleration based on sector progression
        bpm = 115 + (sector_num - 1) * 7 if sector_num < 6 else 152
        step_interval_ms = (60.0 / bpm / 4.0) * 1000.0

        now = pygame.time.get_ticks()
        if now - self.last_tick >= step_interval_ms:
            self.last_tick = now

            # Root key shifts down to darker minor mode in Sector 06 Boss Encounter
            root_offset = -12 if sector_num == 6 else -9

            # Lead Arpeggio voice
            lead_semi = self.lead_pattern[self.step] + root_offset
            lead_freq = self.note_to_freq(lead_semi)
            lead_snd = self.get_tone(lead_freq, 0.08, "saw", 0.07 if sector_num < 6 else 0.10)
            self.channel_lead.play(lead_snd)

            # Bass pulse voice
            bass_semi = self.bass_pattern[self.step]
            if bass_semi != -1:
                bass_freq = self.note_to_freq(bass_semi - 24 + root_offset)
                bass_snd = self.get_tone(bass_freq, 0.16, "square", 0.14)
                self.channel_bass.play(bass_snd)

            self.step = (self.step + 1) % 16


# -------------------------------------------------------------
# 4. Particle Systems & Damage Floaters
# -------------------------------------------------------------
class FloatText:
    def __init__(self, pos, text, color):
        self.pos = Vector2(pos)
        self.text = text
        self.color = color
        self.life = 1.0

    def update(self):
        self.pos.y -= 1.1
        self.life -= 0.02

    def draw(self, surf):
        if self.life > 0:
            rend = FONT_UI.render(self.text, True, self.color)
            rend.set_alpha(int(255 * self.life))
            surf.blit(rend, (self.pos.x - rend.get_width() // 2, self.pos.y))


class Particle:
    def __init__(self, pos, color, speed_mult=1.0, life=1.0):
        self.pos = Vector2(pos)
        ang = random.uniform(0, math.pi * 2)
        sp = random.uniform(1.8, 5.2) * speed_mult
        self.vel = Vector2(math.cos(ang) * sp, math.sin(ang) * sp)
        self.color = color
        self.life = life
        self.decay = random.uniform(0.02, 0.045)

    def update(self):
        self.pos += self.vel
        self.vel *= 0.94
        self.life -= self.decay

    def draw(self, surf):
        if self.life > 0:
            rad = max(1, int(4 * self.life))
            glow = pygame.Surface((rad * 4, rad * 4), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*self.color, int(180 * self.life)), (rad * 2, rad * 2), rad + 3)
            surf.blit(glow, (self.pos.x - rad * 2, self.pos.y - rad * 2), special_flags=pygame.BLEND_ADD)
            pygame.draw.circle(surf, self.color, (int(self.pos.x), int(self.pos.y)), rad)


# -------------------------------------------------------------
# 5. Boss & Projectiles: Sector 06 Guardian
# -------------------------------------------------------------
class HomingMissile:
    def __init__(self, pos, target_pos):
        self.pos = Vector2(pos)
        self.vel = (target_pos - self.pos).normalize() * 2.5
        self.speed = 3.6
        self.life = 220
        self.trail = []

    def update(self, target_pos):
        self.life -= 1
        desired = (target_pos - self.pos).normalize() * self.speed
        steer = (desired - self.vel) * 0.05
        self.vel = (self.vel + steer).normalize() * self.speed
        self.pos += self.vel

        self.trail.append(Vector2(self.pos))
        if len(self.trail) > 8:
            self.trail.pop(0)

    def draw(self, surf):
        for i, pt in enumerate(self.trail):
            rad = max(1, int(i * 0.6))
            pygame.draw.circle(surf, (255, 45, 85), (int(pt.x), int(pt.y)), rad)

        glow = pygame.Surface((28, 28), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 45, 85, 140), (14, 14), 12)
        surf.blit(glow, (self.pos.x - 14, self.pos.y - 14), special_flags=pygame.BLEND_ADD)
        pygame.draw.circle(surf, COLOR_WHITE, (int(self.pos.x), int(self.pos.y)), 4)


class CoreGuardian:
    def __init__(self, pos):
        self.pos = Vector2(pos)
        self.vel = Vector2(0, 0)
        self.max_hp = 100
        self.hp = self.max_hp
        self.missile_timer = 0
        self.rotation = 0
        self.pulse = 0
        self.hit_flash = 0
        self.segments = [Vector2(pos) for _ in range(5)]

    def update(self, target_pos, arena):
        self.rotation += 0.03
        self.pulse = math.sin(pygame.time.get_ticks() * 0.005) * 4
        if self.hit_flash > 0:
            self.hit_flash -= 1

        desired = (target_pos - self.pos).normalize() * 1.6
        self.vel += (desired - self.vel) * 0.03
        self.pos += self.vel

        self.segments[0] = Vector2(self.pos)
        for i in range(1, len(self.segments)):
            delta = self.segments[i] - self.segments[i - 1]
            if delta.length() > 0:
                self.segments[i] = self.segments[i - 1] + delta.normalize() * 18

        self.missile_timer += 1
        if self.missile_timer >= 170:
            self.missile_timer = 0
            arena.missiles.append(HomingMissile(self.pos, target_pos))
            SND_MISSILE.play()

    def damage(self, amt):
        self.hp = max(0, self.hp - amt)
        self.hit_flash = 12
        SND_BOSS_HIT.play()

    def draw(self, surf):
        for i, seg in enumerate(reversed(self.segments)):
            idx = len(self.segments) - 1 - i
            rad = 14 + idx * 2
            pygame.draw.circle(surf, COLOR_METAL_DARK, (int(seg.x), int(seg.y)), rad)
            pygame.draw.circle(surf, COLOR_METAL, (int(seg.x), int(seg.y)), rad - 3)

        core_pos = (int(self.pos.x), int(self.pos.y))
        main_rad = int(28 + self.pulse)
        color = COLOR_WHITE if self.hit_flash > 0 else COLOR_RED

        for i in range(4):
            a = self.rotation + i * (math.pi / 2)
            px = self.pos.x + math.cos(a) * (main_rad + 8)
            py = self.pos.y + math.sin(a) * (main_rad + 8)
            pygame.draw.circle(surf, COLOR_METAL, (int(px), int(py)), 6)
            pygame.draw.line(surf, COLOR_RED, self.pos, (px, py), 2)

        glow = pygame.Surface((main_rad * 4, main_rad * 4), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*color, 100), (main_rad * 2, main_rad * 2), main_rad + 6)
        surf.blit(glow, (self.pos.x - main_rad * 2, self.pos.y - main_rad * 2), special_flags=pygame.BLEND_ADD)

        pygame.draw.circle(surf, COLOR_METAL_DARK, core_pos, main_rad)
        pygame.draw.circle(surf, color, core_pos, main_rad - 6)
        pygame.draw.circle(surf, COLOR_WHITE, core_pos, max(2, main_rad // 3))

        # Boss HP Bar
        bar_w = 300
        bar_h = 10
        bx = (WINDOW_SIZE - bar_w) // 2
        by = 44
        pygame.draw.rect(surf, (15, 18, 26), (bx - 2, by - 2, bar_w + 4, bar_h + 4), border_radius=4)
        pct = self.hp / self.max_hp
        pygame.draw.rect(surf, COLOR_RED, (bx, by, int(bar_w * pct), bar_h), border_radius=3)
        lbl = FONT_MINI.render("CORE GUARDIAN INTEGRITY", True, COLOR_WHITE)
        surf.blit(lbl, lbl.get_rect(center=(WINDOW_SIZE // 2, by - 8)))


# -------------------------------------------------------------
# 6. Physical Hazards: Blades & Laser Emitters
# -------------------------------------------------------------
class RealisticSaw:
    def __init__(self, center, radius, speed):
        self.center = Vector2(center) * CELL_SIZE
        self.radius = radius * CELL_SIZE
        self.ang = random.uniform(0, math.pi * 2)
        self.speed = speed
        self.spin = 0
        self.pos = Vector2(0, 0)
        self.update()

    def update(self):
        self.ang += self.speed
        self.spin += 0.25
        self.pos = self.center + Vector2(math.cos(self.ang), math.sin(self.ang)) * self.radius

    def draw(self, surf):
        pygame.draw.circle(surf, (5, 6, 10), (int(self.pos.x + 4), int(self.pos.y + 4)), 18)
        pts = []
        for i in range(12):
            a = self.spin + i * (math.pi / 6)
            r = 18 if i % 2 == 0 else 10
            pts.append((self.pos.x + math.cos(a) * r, self.pos.y + math.sin(a) * r))
        pygame.draw.polygon(surf, COLOR_METAL, pts)
        pygame.draw.polygon(surf, COLOR_RED, pts, 2)
        pygame.draw.circle(surf, COLOR_METAL_DARK, (int(self.pos.x), int(self.pos.y)), 6)
        pygame.draw.circle(surf, COLOR_WHITE, (int(self.pos.x), int(self.pos.y)), 2)


class LaserTripwire:
    def __init__(self, p1, p2, active_interval=160, on_dur=80):
        self.p1 = Vector2(p1) * CELL_SIZE + Vector2(13, 13)
        self.p2 = Vector2(p2) * CELL_SIZE + Vector2(13, 13)
        self.interval = active_interval
        self.on_dur = on_dur
        self.timer = random.randint(0, 80)
        self.active = False

    def update(self):
        self.timer = (self.timer + 1) % self.interval
        self.active = self.timer < self.on_dur

    def draw(self, surf):
        for p in (self.p1, self.p2):
            pygame.draw.rect(surf, COLOR_METAL_DARK, (p.x - 7, p.y - 7, 14, 14), border_radius=3)
            pygame.draw.circle(surf, COLOR_CYAN if self.active else COLOR_METAL, (int(p.x), int(p.y)), 4)

        if self.active:
            beam = pygame.Surface((WINDOW_SIZE, WINDOW_SIZE), pygame.SRCALPHA)
            pygame.draw.line(beam, (0, 245, 255, 90), self.p1, self.p2, 12)
            pygame.draw.line(beam, (0, 245, 255, 200), self.p1, self.p2, 5)
            pygame.draw.line(beam, (255, 255, 255, 255), self.p1, self.p2, 2)
            surf.blit(beam, (0, 0), special_flags=pygame.BLEND_ADD)
        else:
            pygame.draw.line(surf, (35, 45, 60), self.p1, self.p2, 1)


# -------------------------------------------------------------
# 7. Organic Exoskeleton Snake Architecture
# -------------------------------------------------------------
class OrganicSnake:
    def __init__(self):
        self.reset()

    def reset(self):
        self.grid_head = Vector2(8, 12)
        self.prev_grid_head = Vector2(7, 12)
        self.direction = Vector2(1, 0)
        self.grow_pending = False
        self.moved_this_tick = False

        self.joint_dist = 17.0
        start_px = self.grid_head * CELL_SIZE + Vector2(13, 13)
        self.points = [start_px - self.direction * (i * self.joint_dist) for i in range(6)]

    def add_length(self, count=1):
        for _ in range(count):
            tail_dir = (self.points[-1] - self.points[-2]).normalize() if len(self.points) > 1 else Vector2(-1, 0)
            self.points.append(self.points[-1] + tail_dir * self.joint_dist)

    def shrink(self, count=3):
        for _ in range(min(count, max(0, len(self.points) - 5))):
            self.points.pop()

    def step(self):
        self.prev_grid_head = Vector2(self.grid_head)
        self.grid_head += self.direction
        if self.grow_pending:
            self.add_length(1)
            self.grow_pending = False
        self.moved_this_tick = False

    def update_physics(self, progress):
        target_head = self.prev_grid_head.lerp(self.grid_head, min(1.0, progress)) * CELL_SIZE + Vector2(13, 13)
        self.points[0] = target_head

        for i in range(1, len(self.points)):
            delta = self.points[i] - self.points[i - 1]
            dist = delta.length()
            if dist > 0.001:
                self.points[i] = self.points[i - 1] + (delta / dist) * self.joint_dist

    def draw(self, surf):
        total = len(self.points)
        if total < 2:
            return

        shadow_pts = [(p.x + 3, p.y + 4) for p in self.points]
        pygame.draw.lines(surf, (4, 5, 8), False, shadow_pts, 14)
        pygame.draw.lines(surf, (18, 65, 40), False, [(p.x, p.y) for p in self.points], 16)

        for i in range(total - 1, -1, -1):
            pt = self.points[i]
            taper = 1.0 - (i / total) * 0.6
            rad = max(4, int(11 * taper))

            if i > 0 and i % 2 == 0:
                dir_vec = (self.points[i - 1] - pt)
                if dir_vec.length() > 0:
                    perp = Vector2(-dir_vec.y, dir_vec.x).normalize() * (rad + 5)
                    pygame.draw.line(surf, (0, 245, 255), pt - perp, pt + perp, 2)

            pygame.draw.circle(surf, (15, 35, 25), (int(pt.x), int(pt.y)), rad + 1)
            pygame.draw.circle(surf, COLOR_GREEN if i > 0 else COLOR_CYAN, (int(pt.x), int(pt.y)), rad)
            pygame.draw.circle(surf, (220, 255, 230), (int(pt.x - 2), int(pt.y - 2)), max(1, rad // 3))

        head = self.points[0]
        fwd = (self.points[0] - self.points[1]).normalize() if len(self.points) > 1 else self.direction
        side = Vector2(-fwd.y, fwd.x) * 5
        for s in (-1, 1):
            eye_pos = head + fwd * 4 + side * s
            pygame.draw.circle(surf, (255, 255, 255), (int(eye_pos.x), int(eye_pos.y)), 4)
            top_pupil = eye_pos + Vector2(-fwd.y, fwd.x) * 2
            bot_pupil = eye_pos - Vector2(-fwd.y, fwd.x) * 2
            pygame.draw.line(surf, (10, 15, 22), top_pupil, bot_pupil, 2)


# -------------------------------------------------------------
# 8. Profile & Persistence Engine
# -------------------------------------------------------------
class ProfileManager:
    DB_FILE = "profiles.json"

    def __init__(self):
        self.profiles = self.load()
        self.active_user = None

    def load(self):
        if os.path.exists(self.DB_FILE):
            try:
                with open(self.DB_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save(self):
        try:
            with open(self.DB_FILE, "w") as f:
                json.dump(self.profiles, f, indent=2)
        except Exception:
            pass

    def login_or_create(self, name):
        name = name.strip().upper()
        if not name:
            name = "AGENT_01"
        self.active_user = name
        if name not in self.profiles:
            self.profiles[name] = {"high_score": 0, "max_sector": 1, "guardian_slain": False, "best_boss_time": None}
            self.save()
        return self.profiles[name]

    def update_progress(self, score, sector, boss_beaten=False, boss_time=None):
        if not self.active_user:
            return
        data = self.profiles[self.active_user]
        data["high_score"] = max(data["high_score"], score)
        data["max_sector"] = max(data["max_sector"], sector)
        if boss_beaten:
            data["guardian_slain"] = True
            if boss_time is not None:
                cur = data.get("best_boss_time")
                if cur is None or boss_time < cur:
                    data["best_boss_time"] = round(boss_time, 2)
        self.save()


# -------------------------------------------------------------
# 9. Game Director & Master State Machine
# -------------------------------------------------------------
class GameDirector:
    def __init__(self):
        self.pm = ProfileManager()
        self.arp = CyberArpeggiator()
        self.state = "LOGIN"  # LOGIN -> MENU -> HANGAR -> GUIDE -> PLAYING -> WIN -> GAMEOVER
        self.name_buffer = ""
        self.sector = 1
        self.score = 0
        self.high_score = 0
        self.is_boss_rush = False
        self.boss_start_time = 0
        self.final_boss_time = 0

        self.snake = OrganicSnake()
        self.particles = []
        self.float_texts = []
        self.saws = []
        self.lasers = []
        self.missiles = []
        self.boss = None

        self.shake = 0
        self.slow_timer = 0
        self.core_pos = Vector2(0, 0)
        self.core_type = "red"
        self.core_timer = 0

        self.last_step_time = pygame.time.get_ticks()
        self.base_delay = 130
        self.sector_targets = {1: 6, 2: 9, 3: 12, 4: 15, 5: 18, 6: 999}

    def start_campaign(self, sec=1, is_rush=False):
        rec = self.pm.profiles[self.pm.active_user]
        self.high_score = rec["high_score"]
        self.is_boss_rush = is_rush
        self.score = 0
        self.sector = sec
        if is_rush or sec == 6:
            self.boss_start_time = time.time()
        self.build_sector(sec)

    def build_sector(self, sec):
        self.sector = sec
        self.saws.clear()
        self.lasers.clear()
        self.missiles.clear()
        self.boss = None
        self.snake.reset()
        self.base_delay = max(65, 130 - (sec - 1) * 12)

        if sec == 2:
            self.saws = [RealisticSaw((5, 5), 2.5, 0.04), RealisticSaw((18, 18), 2.5, -0.04)]
        elif sec == 3:
            self.lasers = [LaserTripwire((3, 7), (20, 7), 160, 80), LaserTripwire((3, 16), (20, 16), 160, 80)]
        elif sec == 4:
            self.saws = [RealisticSaw((12, 12), 6.0, 0.035)]
            self.lasers = [LaserTripwire((12, 4), (12, 19), 140, 70)]
        elif sec == 5:
            self.lasers = [LaserTripwire((4, 4), (19, 19), 150, 75), LaserTripwire((19, 4), (4, 19), 150, 75)]
            self.saws = [RealisticSaw((6, 6), 2.5, 0.05), RealisticSaw((17, 17), 2.5, -0.05)]
        elif sec == 6:
            self.boss = CoreGuardian((WINDOW_SIZE // 2, 120))
            self.lasers = [
                LaserTripwire((4, 6), (19, 6), 180, 100),
                LaserTripwire((4, 17), (19, 17), 180, 100),
            ]

        self.spawn_core()

    def spawn_core(self):
        types = ["red", "red", "red", "gold", "shrink", "slow"]
        self.core_type = random.choice(types)
        self.core_timer = 200 if self.core_type != "red" else 0
        while True:
            c = Vector2(random.randint(2, CELL_COUNT - 3), random.randint(3, CELL_COUNT - 3))
            if c != self.snake.grid_head:
                self.core_pos = c
                break

    def trigger_crash(self):
        self.state = "GAMEOVER"
        self.shake = 24
        SND_CRASH.play()
        hp = self.snake.points[0]
        for _ in range(50):
            self.particles.append(Particle(hp, COLOR_RED, 2.2))

    def trigger_win(self):
        self.state = "WIN"
        SND_PORTAL.play()
        is_boss_slain = self.sector == 6
        boss_clear_time = (time.time() - self.boss_start_time) if is_boss_slain else None
        if is_boss_slain:
            self.final_boss_time = boss_clear_time
        self.pm.update_progress(self.score, self.sector + 1, boss_beaten=is_boss_slain, boss_time=boss_clear_time)
        hp = self.snake.points[0]
        for _ in range(50):
            self.particles.append(Particle(hp, COLOR_GOLD, 2.0))

    def tick_logic(self):
        if self.state != "PLAYING":
            return
        self.snake.step()
        head = self.snake.grid_head

        # Core collisions
        if head == self.core_pos:
            hx = head * CELL_SIZE + Vector2(13, 13)
            if self.core_type == "red":
                self.score += 1
                self.snake.grow_pending = True
                self.float_texts.append(FloatText(hx, "+1", COLOR_RED))
                SND_EAT.play()
            elif self.core_type == "gold":
                self.score += 5
                self.snake.grow_pending = True
                self.float_texts.append(FloatText(hx, "+5 OVERCHARGE", COLOR_GOLD))
                SND_SPECIAL.play()
            elif self.core_type == "shrink":
                self.score += 2
                self.snake.shrink(3)
                self.float_texts.append(FloatText(hx, "PURGE TAIL", COLOR_CYAN))
                SND_SPECIAL.play()
            elif self.core_type == "slow":
                self.slow_timer = 140
                self.float_texts.append(FloatText(hx, "TIME DILATION", COLOR_PURPLE))
                SND_SPECIAL.play()

            for _ in range(20):
                self.particles.append(Particle(hx, COLOR_GOLD if self.core_type == "gold" else COLOR_CYAN))

            if self.score > self.high_score:
                self.high_score = self.score
                self.pm.update_progress(self.score, self.sector)

            if self.sector < 6 and self.score >= self.sector_targets[self.sector]:
                self.trigger_win()
                return

            self.spawn_core()

        # Wall collisions
        if not (0 <= head.x < CELL_COUNT and 0 <= head.y < CELL_COUNT):
            self.trigger_crash()
            return

        # Self collisions
        hp_head = self.snake.points[0]
        for pt in self.snake.points[4:]:
            if hp_head.distance_to(pt) < 13:
                self.trigger_crash()
                return

    def update_frame(self):
        # Drive background arpeggiator
        if self.state in ("PLAYING", "WIN", "GAMEOVER"):
            self.arp.update(self.sector)
        else:
            self.arp.update(1)

        now = pygame.time.get_ticks()
        delay = 200 if self.slow_timer > 0 else self.base_delay
        if self.slow_timer > 0:
            self.slow_timer -= 1

        if now - self.last_step_time >= delay:
            self.tick_logic()
            self.last_step_time = now

        progress = (now - self.last_step_time) / delay
        self.snake.update_physics(progress)

        for s in self.saws:
            s.update()
        for l in self.lasers:
            l.update()

        head_px = self.snake.points[0]

        # Sector 06 Boss Loop
        if self.boss and self.state == "PLAYING":
            self.boss.update(head_px, self)
            if head_px.distance_to(self.boss.pos) < 36:
                self.trigger_crash()
                return
            for l in self.lasers:
                if l.active:
                    l2 = l.p1.distance_squared_to(l.p2)
                    t = max(0, min(1, (self.boss.pos - l.p1).dot(l.p2 - l.p1) / l2))
                    proj = l.p1 + t * (l.p2 - l.p1)
                    if self.boss.pos.distance_to(proj) < 32:
                        self.boss.damage(1.4)
                        self.shake = 6
                        for _ in range(6):
                            self.particles.append(Particle(self.boss.pos, COLOR_CYAN, 1.5))
                        if self.boss.hp <= 0:
                            self.trigger_win()
                            return

        for m in self.missiles[:]:
            m.update(head_px)
            if head_px.distance_to(m.pos) < 16:
                self.trigger_crash()
                return
            if m.life <= 0:
                self.missiles.remove(m)

        if self.state == "PLAYING":
            for s in self.saws:
                if head_px.distance_to(s.pos) < 22:
                    self.trigger_crash()
                    return
            for l in self.lasers:
                if l.active:
                    l2 = l.p1.distance_squared_to(l.p2)
                    t = max(0, min(1, (head_px - l.p1).dot(l.p2 - l.p1) / l2))
                    proj = l.p1 + t * (l.p2 - l.p1)
                    if head_px.distance_to(proj) < 12:
                        self.trigger_crash()
                        return

        if self.core_timer > 0:
            self.core_timer -= 1
            if self.core_timer <= 0:
                self.spawn_core()

        for p in self.particles[:]:
            p.update()
            if p.life <= 0:
                self.particles.remove(p)

        for ft in self.float_texts[:]:
            ft.update()
            if ft.life <= 0:
                self.float_texts.remove(ft)

        if self.shake > 0:
            self.shake -= 1

    def draw_arena_grid(self, surf):
        surf.fill(COLOR_VOID)
        for r in range(CELL_COUNT):
            for c in range(CELL_COUNT):
                col = COLOR_GRID_LIGHT if (r + c) % 2 == 0 else COLOR_GRID_DARK
                rect = pygame.Rect(c * CELL_SIZE, r * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(surf, col, rect)
                pygame.draw.rect(surf, (10, 12, 18), rect, 1)

    def draw(self, surf):
        self.draw_arena_grid(surf)

        for s in self.saws:
            s.draw(surf)
        for l in self.lasers:
            l.draw(surf)
        for m in self.missiles:
            m.draw(surf)
        if self.boss:
            self.boss.draw(surf)

        # Draw Energy Core
        cp = self.core_pos * CELL_SIZE + Vector2(13, 13)
        col_map = {"red": COLOR_RED, "gold": COLOR_GOLD, "shrink": COLOR_CYAN, "slow": COLOR_PURPLE}
        c_col = col_map[self.core_type]
        p_pulse = math.sin(pygame.time.get_ticks() * 0.008) * 3
        r = max(4, int(10 + p_pulse))
        glow = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*c_col, 100), (r * 2, r * 2), r + 4)
        surf.blit(glow, (cp.x - r * 2, cp.y - r * 2), special_flags=pygame.BLEND_ADD)
        pygame.draw.circle(surf, c_col, (int(cp.x), int(cp.y)), r)

        self.snake.draw(surf)
        for p in self.particles:
            p.draw(surf)
        for ft in self.float_texts:
            ft.draw(surf)

        # Master HUD
        hud = pygame.Surface((WINDOW_SIZE, 36), pygame.SRCALPHA)
        hud.fill((8, 10, 15, 220))
        surf.blit(hud, (0, 0))

        if self.sector == 6 or self.is_boss_rush:
            cur_time = time.time() - self.boss_start_time if self.state == "PLAYING" else self.final_boss_time
            sec_str = f"SECTOR 06 // BOSS RUSH [{cur_time:.1f}s]"
        else:
            sec_str = f"SECTOR 0{self.sector}"

        t_hud = f"[{self.pm.active_user}] {sec_str} // SCORE: {self.score} // RECORD: {self.high_score}"
        surf.blit(FONT_UI.render(t_hud, True, COLOR_CYAN), (14, 10))

        # Modals
        if self.state == "LOGIN":
            self.render_login(surf)
        elif self.state == "MENU":
            self.render_menu(surf)
        elif self.state == "HANGAR":
            self.render_hangar(surf)
        elif self.state == "GUIDE":
            self.render_guide(surf)
        elif self.state == "WIN":
            if self.sector == 6:
                title = f"GUARDIAN DEFEATED! [{self.final_boss_time:.2f}s]"
                btn = "PRESS SPACE TO ENTER HANGAR"
            else:
                title = f"SECTOR 0{self.sector} PURGED"
                btn = "PRESS SPACE FOR NEXT SECTOR"
            self.render_modal(surf, title, COLOR_GOLD, btn)
        elif self.state == "GAMEOVER":
            self.render_modal(surf, "SYSTEM BREACHED", COLOR_RED, "PRESS SPACE TO REBOOT SECTOR")

    def render_login(self, surf):
        ov = pygame.Surface((WINDOW_SIZE, WINDOW_SIZE), pygame.SRCALPHA)
        ov.fill((6, 7, 11, 245))
        surf.blit(ov, (0, 0))

        t = FONT_TITLE.render("PILOT IDENTIFICATION", True, COLOR_CYAN)
        surf.blit(t, t.get_rect(center=(WINDOW_SIZE // 2, 170)))

        sub = FONT_SUB.render("Enter Callsign & Press ENTER:", True, COLOR_WHITE)
        surf.blit(sub, sub.get_rect(center=(WINDOW_SIZE // 2, 250)))

        box = pygame.Rect(WINDOW_SIZE // 2 - 140, 290, 280, 48)
        pygame.draw.rect(surf, COLOR_METAL_DARK, box, border_radius=6)
        pygame.draw.rect(surf, COLOR_CYAN, box, 2, border_radius=6)

        cursor = "_" if (pygame.time.get_ticks() // 500) % 2 == 0 else ""
        txt = FONT_SUB.render(self.name_buffer + cursor, True, COLOR_WHITE)
        surf.blit(txt, txt.get_rect(center=box.center))

    def render_menu(self, surf):
        ov = pygame.Surface((WINDOW_SIZE, WINDOW_SIZE), pygame.SRCALPHA)
        ov.fill((6, 7, 11, 240))
        surf.blit(ov, (0, 0))

        title = FONT_TITLE.render("CYBERSNAKE: APEX", True, COLOR_CYAN)
        surf.blit(title, title.get_rect(center=(WINDOW_SIZE // 2, 130)))

        data = self.pm.profiles.get(self.pm.active_user, {})
        status = "GUARDIAN DEFEATED" if data.get("guardian_slain") else f"UNLOCKED SECTOR: 0{data.get('max_sector', 1)}"
        sub = FONT_UI.render(f"PILOT: {self.pm.active_user} // {status}", True, COLOR_GOLD)
        surf.blit(sub, sub.get_rect(center=(WINDOW_SIZE // 2, 185)))

        mouse_pos = pygame.mouse.get_pos()

        # Button 1: Initiate Campaign
        btn1 = pygame.Rect(WINDOW_SIZE // 2 - 140, 240, 280, 50)
        h1 = btn1.collidepoint(mouse_pos)
        pygame.draw.rect(surf, COLOR_CYAN if h1 else COLOR_METAL_DARK, btn1, border_radius=6)
        pygame.draw.rect(surf, COLOR_CYAN, btn1, 2, border_radius=6)
        surf.blit(FONT_SUB.render("COMMENCE CAMPAIGN", True, COLOR_VOID if h1 else COLOR_WHITE),
                  FONT_SUB.render("COMMENCE CAMPAIGN", True, COLOR_VOID if h1 else COLOR_WHITE).get_rect(center=btn1.center))

        # Button 2: Hangar Terminal / Sector Select
        btn2 = pygame.Rect(WINDOW_SIZE // 2 - 140, 310, 280, 50)
        h2 = btn2.collidepoint(mouse_pos)
        pygame.draw.rect(surf, COLOR_GOLD if h2 else COLOR_METAL_DARK, btn2, border_radius=6)
        pygame.draw.rect(surf, COLOR_GOLD, btn2, 2, border_radius=6)
        surf.blit(FONT_SUB.render("HANGAR // SELECT", True, COLOR_VOID if h2 else COLOR_WHITE),
                  FONT_SUB.render("HANGAR // SELECT", True, COLOR_VOID if h2 else COLOR_WHITE).get_rect(center=btn2.center))

    def render_hangar(self, surf):
        ov = pygame.Surface((WINDOW_SIZE, WINDOW_SIZE), pygame.SRCALPHA)
        ov.fill((6, 7, 11, 245))
        surf.blit(ov, (0, 0))

        title = FONT_TITLE.render("HANGAR TERMINAL", True, COLOR_GOLD)
        surf.blit(title, title.get_rect(center=(WINDOW_SIZE // 2, 60)))

        data = self.pm.profiles.get(self.pm.active_user, {})
        max_sec = data.get("max_sector", 1)
        best_t = data.get("best_boss_time", "N/A")

        info_t = FONT_UI.render(f"PILOT CALLSIGN: {self.pm.active_user} | BEST BOSS TRIAL: {best_t}s", True, COLOR_CYAN)
        surf.blit(info_t, info_t.get_rect(center=(WINDOW_SIZE // 2, 105)))

        mouse_pos = pygame.mouse.get_pos()

        # Sector 01-05 Grid Buttons
        for i in range(1, 6):
            col = (i - 1) % 3
            row = (i - 1) // 3
            bx = 80 + col * 165
            by = 150 + row * 90
            rect = pygame.Rect(bx, by, 145, 65)

            unlocked = i <= max_sec
            h = rect.collidepoint(mouse_pos) and unlocked

            bg_c = COLOR_CYAN if h else (COLOR_METAL_DARK if unlocked else (18, 20, 26))
            pygame.draw.rect(surf, bg_c, rect, border_radius=6)
            pygame.draw.rect(surf, COLOR_CYAN if unlocked else (40, 45, 55), rect, 2, border_radius=6)

            txt = FONT_SUB.render(f"SECTOR 0{i}", True, COLOR_VOID if h else (COLOR_WHITE if unlocked else (80, 90, 105)))
            stat = FONT_MINI.render("AUTHORIZED" if unlocked else "LOCKED", True, COLOR_GOLD if unlocked else (80, 90, 105))
            surf.blit(txt, (bx + 12, by + 12))
            surf.blit(stat, (bx + 12, by + 40))

        # Sector 06 Timed Boss Rush Card
        boss_btn = pygame.Rect(80, 350, 475, 75)
        boss_unlocked = max_sec >= 6 or data.get("guardian_slain", False)
        h_boss = boss_btn.collidepoint(mouse_pos) and boss_unlocked

        pygame.draw.rect(surf, COLOR_RED if h_boss else (COLOR_METAL_DARK if boss_unlocked else (18, 20, 26)), boss_btn, border_radius=8)
        pygame.draw.rect(surf, COLOR_RED if boss_unlocked else (50, 55, 65), boss_btn, 2, border_radius=8)

        b_title = FONT_SUB.render("SECTOR 06 // TIMED BOSS RUSH", True, COLOR_VOID if h_boss else (COLOR_WHITE if boss_unlocked else (80, 90, 105)))
        b_sub = FONT_UI.render("CORE GUARDIAN TRIAL // TIMED RUN", True, COLOR_VOID if h_boss else (COLOR_GOLD if boss_unlocked else (80, 90, 105)))
        surf.blit(b_title, (105, 365))
        surf.blit(b_sub, (105, 395))

        # Return to main menu prompt
        prompt = FONT_UI.render("PRESS ESC TO RETURN TO MAIN MENU", True, (150, 160, 180))
        surf.blit(prompt, prompt.get_rect(center=(WINDOW_SIZE // 2, 570)))

    def render_guide(self, surf):
        ov = pygame.Surface((WINDOW_SIZE, WINDOW_SIZE), pygame.SRCALPHA)
        ov.fill((6, 7, 11, 245))
        surf.blit(ov, (0, 0))

        title = FONT_SUB.render("TACTICAL PROTOCOL", True, COLOR_CYAN)
        surf.blit(title, title.get_rect(center=(WINDOW_SIZE // 2, 70)))

        intel = [
            ("CONTROLS: WASD or Arrow Keys", COLOR_WHITE),
            ("", COLOR_WHITE),
            ("SECTOR 06 TACTICS (THE GUARDIAN):", COLOR_RED),
            ("• The Core Guardian tracks and charges your coordinates.", COLOR_WHITE),
            ("• Heat-seeking missiles are fired on cycles. Dodge them!", COLOR_WHITE),
            ("• Bait the Guardian into high-voltage Lasers to damage it.", COLOR_CYAN),
            ("", COLOR_WHITE),
            ("POWER MODULES:", COLOR_GOLD),
            ("• Cyan: Tail Purge  |  Purple: Time Dilation  |  Gold: +5 Pts", COLOR_WHITE),
        ]
        y = 140
        for line, c in intel:
            surf.blit(FONT_UI.render(line, True, c), (50, y))
            y += 26

        prompt = FONT_SUB.render("PRESS SPACE TO ENGAGE", True, COLOR_GREEN)
        surf.blit(prompt, prompt.get_rect(center=(WINDOW_SIZE // 2, 530)))

    def render_modal(self, surf, title, color, prompt):
        ov = pygame.Surface((WINDOW_SIZE, WINDOW_SIZE), pygame.SRCALPHA)
        ov.fill((6, 7, 11, 230))
        surf.blit(ov, (0, 0))
        t = FONT_TITLE.render(title, True, color)
        p = FONT_SUB.render(prompt, True, COLOR_WHITE)
        surf.blit(t, t.get_rect(center=(WINDOW_SIZE // 2, WINDOW_SIZE // 2 - 25)))
        surf.blit(p, p.get_rect(center=(WINDOW_SIZE // 2, WINDOW_SIZE // 2 + 30)))


# -------------------------------------------------------------
# 10. Execution Loop & Event Router
# -------------------------------------------------------------
director = GameDirector()
canvas = pygame.Surface((WINDOW_SIZE, WINDOW_SIZE))

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if director.state == "LOGIN":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and director.name_buffer.strip():
                    director.pm.login_or_create(director.name_buffer)
                    director.state = "MENU"
                elif event.key == pygame.K_BACKSPACE:
                    director.name_buffer = director.name_buffer[:-1]
                elif len(director.name_buffer) < 12 and event.unicode.isalnum():
                    director.name_buffer += event.unicode.upper()

        elif director.state == "MENU":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                btn1 = pygame.Rect(WINDOW_SIZE // 2 - 140, 240, 280, 50)
                btn2 = pygame.Rect(WINDOW_SIZE // 2 - 140, 310, 280, 50)
                if btn1.collidepoint(event.pos):
                    SND_SPECIAL.play()
                    director.state = "GUIDE"
                elif btn2.collidepoint(event.pos):
                    SND_SPECIAL.play()
                    director.state = "HANGAR"

        elif director.state == "HANGAR":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                director.state = "MENU"

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                data = director.pm.profiles.get(director.pm.active_user, {})
                max_sec = data.get("max_sector", 1)

                # Sectors 01-05
                for i in range(1, 6):
                    col = (i - 1) % 3
                    row = (i - 1) // 3
                    rect = pygame.Rect(80 + col * 165, 150 + row * 90, 145, 65)
                    if rect.collidepoint(event.pos) and i <= max_sec:
                        SND_PORTAL.play()
                        director.start_campaign(sec=i, is_rush=False)
                        director.state = "PLAYING"
                        break

                # Sector 06 Timed Boss Trial
                boss_btn = pygame.Rect(80, 350, 475, 75)
                boss_unlocked = max_sec >= 6 or data.get("guardian_slain", False)
                if boss_btn.collidepoint(event.pos) and boss_unlocked:
                    SND_PORTAL.play()
                    director.start_campaign(sec=6, is_rush=True)
                    director.state = "PLAYING"

        elif director.state == "GUIDE":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                director.start_campaign(sec=1, is_rush=False)
                director.state = "PLAYING"

        elif director.state == "WIN":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                if director.is_boss_rush or director.sector == 6:
                    director.state = "HANGAR"
                else:
                    director.score = 0
                    director.build_sector(director.sector + 1)
                    director.state = "PLAYING"

        elif director.state == "GAMEOVER":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                director.score = 0
                if director.is_boss_rush:
                    director.boss_start_time = time.time()
                director.build_sector(director.sector)
                director.state = "PLAYING"

        elif director.state == "PLAYING":
            if event.type == pygame.KEYDOWN and not director.snake.moved_this_tick:
                d = director.snake.direction
                if (event.key in (pygame.K_UP, pygame.K_w)) and d.y != 1:
                    director.snake.direction = Vector2(0, -1)
                    director.snake.moved_this_tick = True
                elif (event.key in (pygame.K_DOWN, pygame.K_s)) and d.y != -1:
                    director.snake.direction = Vector2(0, 1)
                    director.snake.moved_this_tick = True
                elif (event.key in (pygame.K_LEFT, pygame.K_a)) and d.x != 1:
                    director.snake.direction = Vector2(-1, 0)
                    director.snake.moved_this_tick = True
                elif (event.key in (pygame.K_RIGHT, pygame.K_d)) and d.x != -1:
                    director.snake.direction = Vector2(1, 0)
                    director.snake.moved_this_tick = True

    director.update_frame()
    director.draw(canvas)

    ox, oy = (random.randint(-4, 4), random.randint(-4, 4)) if director.shake > 0 else (0, 0)
    screen.fill((0, 0, 0))
    screen.blit(canvas, (ox, oy))
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()