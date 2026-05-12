import pygame, sys, random

pygame.init()

WIDTH, HEIGHT = 1200, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Stickman Jump")
clock = pygame.time.Clock()

font = pygame.font.SysFont(None, 70)
small_font = pygame.font.SysFont(None, 40)
tiny_font = pygame.font.SysFont(None, 28)

WHITE=(255,255,255); BLACK=(0,0,0); BLUE=(50,150,255); GREEN=(50,200,50)
YELLOW=(255,215,0); RED=(200,50,50); ORANGE=(255,100,0); DARK_RED=(120,0,0)
PURPLE=(150,80,220); CYAN=(0,220,255); PINK=(255,80,180); BROWN=(140,80,30)
GRAY=(100,100,100); ICE_BLUE=(120,220,255); GHOST_GRAY=(170,170,170)

try:
    background = pygame.image.load("stickman1.jpg").convert()
    background = pygame.transform.scale(background, (WIDTH, HEIGHT))
except FileNotFoundError:
    background = pygame.Surface((WIDTH, HEIGHT))
    background.fill((135, 206, 235))

bg_x = 0
bg_scroll_speed = 2

SPRITE_SIZE = 300
run_frames = []
try:
    for i in range(1, 7):
        img = pygame.image.load(f"run{i}.png").convert_alpha()
        img = pygame.transform.scale(img, (SPRITE_SIZE, SPRITE_SIZE))
        run_frames.append(img)
except FileNotFoundError:
    for i in range(6):
        surf = pygame.Surface((SPRITE_SIZE, SPRITE_SIZE), pygame.SRCALPHA)
        pygame.draw.rect(surf, BLUE, (125, 200, 50, 100))
        run_frames.append(surf)

frame_index = 0
animation_speed = 0.2
facing_right = True

LAVA_HEIGHT = 45
lava_rect = pygame.Rect(0, HEIGHT - LAVA_HEIGHT, WIDTH, LAVA_HEIGHT)

high_score = 0
total_coins = 0
total_deaths = 0
total_kills = 0
best_kills = 0
runs_played = 0

upgrades = {
    "speed": 0,
    "jump": 0,
    "weapon": 0,
    "fire_rate": 0,
    "shield": 0,
    "max_lives": 0,
    "totem": 0,
    "coin_spawn": 0,
}

upgrade_prices = {
    # Ceny jsou zhruba o 50 % nižší než předtím,
    # ale každý další level postupně zdražuje.
    "speed": [8, 20, 45, 80],
    "jump": [12, 30, 65, 110],
    "weapon": [50],
    "fire_rate": [25, 60, 125, 200],
    "shield": [40, 90, 175, 275],
    "max_lives": [20, 45, 80, 125, 180, 250, 350, 475],
    "coin_spawn": [30, 70, 140, 250, 425],
    "totem": [600],
}

def clamp(v, a, b):
    return max(a, min(v, b))

def get_speed():
    return 6.5 + upgrades["speed"] * 1.3

def get_jump_power():
    return -15 - upgrades["jump"] * 1.6

def get_shield_time():
    return 600 + upgrades["shield"] * 180

def get_fire_cooldown():
    return max(8, 35 - upgrades["fire_rate"] * 6)

def get_start_lives():
    return 2 + upgrades["max_lives"]

def get_coin_bonus():
    return upgrades["coin_spawn"]

def get_upgrade_price(name):
    level = upgrades[name]
    return None if level >= len(upgrade_prices[name]) else upgrade_prices[name][level]

def buy_upgrade(name):
    global total_coins
    price = get_upgrade_price(name)
    if price is not None and total_coins >= price:
        total_coins -= price
        upgrades[name] += 1

def rect_overlaps_any(rect, rects, padding=20):
    test = rect.inflate(padding, padding)
    return any(test.colliderect(r) for r in rects)

def make_platform(x, y, w, h=40, moving=False, platform_type="normal"):
    return {
        "rect": pygame.Rect(x, y, w, h),
        "scored": False,
        "type": platform_type,
        "moving": moving,
        "move_offset": 0,
        "move_range": random.randint(60, 140),
        "move_speed": random.choice([1, 1.5, 2]),
        "move_dir": random.choice([-1, 1]),
        "visible": True,
        "disappear_timer": random.randint(0, 300),
    }

def make_ladder(x, y_top, y_bottom):
    return pygame.Rect(x, y_top, 45, y_bottom - y_top)

def spawn_enemy(platform_rect):
    w, h = 50, 50
    x = random.randint(platform_rect.x, platform_rect.x + platform_rect.width - w)
    return {"type": "ground", "rect": pygame.Rect(x, platform_rect.y - h, w, h),
            "speed": random.choice([-2, 2]), "platform": platform_rect}

def spawn_flying_enemy(x, y):
    return {"type": "flying", "rect": pygame.Rect(x, y, 55, 45),
            "move_offset": 0, "move_range": random.randint(50, 110),
            "move_speed": random.choice([1, 1.5, 2]), "move_dir": random.choice([-1, 1]),
            "shoot_timer": random.randint(60, 140)}

def shoot_enemy_bullet(enemy):
    enemy_bullets.append({"rect": pygame.Rect(enemy["rect"].left - 18, enemy["rect"].centery - 6, 18, 12), "speed": -8})

def shoot_player_bullet():
    global player_fire_timer
    if upgrades["weapon"] <= 0 or player_fire_timer > 0:
        return
    speed = 13 if facing_right else -13
    x = player.right if facing_right else player.left - 22
    player_bullets.append({"rect": pygame.Rect(x, player.centery - 5, 22, 10), "speed": speed})
    player_fire_timer = get_fire_cooldown()

def create_explosion(x, y):
    explosions.append({"x": x, "y": y, "timer": 20, "radius": 8})

def get_coin_spawn_chance():
    # Mince jsou trochu častější.
    # Level 0 = 35 %, potom se šance postupně zvyšuje.
    chances = [0.35, 0.48, 0.60, 0.72, 0.84, 0.95]
    level = clamp(upgrades["coin_spawn"], 0, len(chances) - 1)
    return chances[level]


def get_coin_count_on_platform():
    # Počet mincí je trochu random podle štěstí.
    # I bez upgradu může občas padnout 2 nebo 3 mince.
    level = upgrades["coin_spawn"]

    if level <= 0:
        return random.choices([1, 2, 3], weights=[70, 25, 5])[0]
    elif level == 1:
        return random.choices([1, 2, 3, 4], weights=[25, 45, 25, 5])[0]
    elif level == 2:
        return random.choices([2, 3, 4, 5], weights=[25, 40, 25, 10])[0]
    elif level == 3:
        return random.choices([3, 4, 5, 6], weights=[25, 35, 25, 15])[0]
    elif level == 4:
        return random.choices([4, 5, 6, 7], weights=[25, 35, 25, 15])[0]
    else:
        return random.choices([5, 6, 7, 8], weights=[20, 35, 30, 15])[0]


def add_coin_line(x, y, width, platform_y):
    # Mince se spawnují uprostřed platformy.
    # Počet záleží na coin upgradu a trochu na štěstí.
    coin_count = get_coin_count_on_platform()
    spacing = 45
    total_width = (coin_count - 1) * spacing
    start_x = x + width // 2 - total_width // 2

    for i in range(coin_count):
        coin = pygame.Rect(start_x + i * spacing, platform_y - 55, 35, 35)

        if (
            coin.left > x + 10
            and coin.right < x + width - 10
            and not rect_overlaps_any(coin, coins, 10)
        ):
            coins.append(coin)

def generate_next_platform():
    global last_main_platform
    last = last_main_platform["rect"]
    diff = min(score / 25, 1)

    w = random.randint(clamp(int(320 - diff * 75), 220, 320), clamp(int(480 - diff * 85), 310, 480))
    gap = random.randint(int(135 + diff * 35), int(220 + diff * 60))
    x = last.right + gap
    y = clamp(last.y + random.randint(-45, 70), 300, HEIGHT - LAVA_HEIGHT - 110)

    platform_type = "normal"
    chance = random.random()
    if score >= 5 and chance < 0.14:
        platform_type = "ice"
    elif score >= 10 and chance < 0.24:
        platform_type = "disappearing"

    moving = random.random() < 0.05 + diff * 0.13
    if platform_type == "disappearing":
        moving = False

    p = make_platform(x, y, w, 40, moving, platform_type)
    platforms.append(p)
    last_main_platform = p

    if random.random() < get_coin_spawn_chance():
        add_coin_line(x, y, w, y)

    if random.random() < 0.22:
        upper_w = random.randint(220, 350)
        upper_x = x + random.randint(20, max(21, w - upper_w - 20)) if w > upper_w + 40 else x + 20
        upper_y = clamp(y - random.randint(105, 145), 190, y - 95)
        upper_rect = pygame.Rect(upper_x, upper_y, upper_w, 35)
        if not rect_overlaps_any(upper_rect, [pl["rect"] for pl in platforms], 35):
            upper = make_platform(upper_x, upper_y, upper_w, 35, False, "normal")
            platforms.append(upper)
            ladder = make_ladder(upper_x + upper_w // 2 - 20, upper_y + 35, y)
            if not rect_overlaps_any(ladder, ladders, 10):
                ladders.append(ladder)
            if random.random() < get_coin_spawn_chance():
                add_coin_line(upper_x, upper_y, upper_w, upper_y)

    if w > 220 and random.random() < 0.20 + diff * 0.28:
        e = spawn_enemy(p["rect"])
        if not rect_overlaps_any(e["rect"], [en["rect"] for en in enemies], 30):
            enemies.append(e)

    if random.random() < 0.05 + diff * 0.14:
        fly = spawn_flying_enemy(x + w + random.randint(80, 180), random.randint(140, max(150, y - 130)))
        if not rect_overlaps_any(fly["rect"], [en["rect"] for en in enemies], 80):
            enemies.append(fly)

    if random.randint(1, 100) == 1:
        shield = pygame.Rect(x + w // 2 - 20, y - 95, 40, 40)
        if not rect_overlaps_any(shield, coins + shield_powerups, 25):
            shield_powerups.append(shield)

def reset_game():
    hitbox_w, hitbox_h = 35, 70
    p = pygame.Rect(200, HEIGHT - LAVA_HEIGHT - 120, hitbox_w, hitbox_h)

    plats = [
        make_platform(0, HEIGHT - LAVA_HEIGHT - 50, 500),
        make_platform(560, HEIGHT - 245, 360),
        make_platform(1020, HEIGHT - 300, 330),
        make_platform(1450, HEIGHT - 355, 310),
    ]
    plats[0]["scored"] = True
    last = plats[-1]

    cs, ens, eb, pb, exps, shields, lads = [], [], [], [], [], [], []
    upper = make_platform(250, HEIGHT - LAVA_HEIGHT - 200, 260, 35)
    plats.append(upper)
    lads.append(make_ladder(355, HEIGHT - LAVA_HEIGHT - 200 + 35, HEIGHT - LAVA_HEIGHT - 50))

    return (p, plats, cs, ens, eb, pb, exps, shields, lads, last, 0, 0, 0, get_start_lives(), 0, 0, 0, upgrades["totem"])

(player, platforms, coins, enemies, enemy_bullets, player_bullets, explosions,
 shield_powerups, ladders, last_main_platform, score, coins_collected, kills,
 lives, invincible_timer, bonus_life_coins, shield_timer, totems_available) = reset_game()

player_vel_y = 0
gravity = 0.6
on_ground = False
scroll_speed = 10
coyote_timer = 0
coyote_time_max = 8
jump_buffer = 0
jump_buffer_max = 8
player_fire_timer = 0
game_state = "menu"
paused = False

start_button = pygame.Rect(WIDTH // 2 - 110, 235, 220, 60)
shop_button = pygame.Rect(WIDTH // 2 - 110, 315, 220, 60)
leaderboard_button = pygame.Rect(WIDTH // 2 - 110, 395, 220, 60)
back_button = pygame.Rect(40, 40, 150, 55)
restart_button = pygame.Rect(WIDTH // 2 - 130, 540, 260, 65)
game_over_menu_button = pygame.Rect(WIDTH // 2 - 130, 620, 260, 65)

shop_buttons = {
    "speed": pygame.Rect(270, 175, 660, 50),
    "jump": pygame.Rect(270, 235, 660, 50),
    "weapon": pygame.Rect(270, 295, 660, 50),
    "fire_rate": pygame.Rect(270, 355, 660, 50),
    "shield": pygame.Rect(270, 415, 660, 50),
    "max_lives": pygame.Rect(270, 475, 660, 50),
    "coin_spawn": pygame.Rect(270, 535, 660, 50),
    "totem": pygame.Rect(270, 595, 660, 50),
}

def draw_background():
    screen.blit(background, (bg_x, 0))
    screen.blit(background, (bg_x + WIDTH, 0))

def draw_lava():
    pygame.draw.rect(screen, DARK_RED, lava_rect)
    for x in range(0, WIDTH, 40):
        pygame.draw.circle(screen, ORANGE, (x, lava_rect.y + random.randint(4, 15)), 18)

def draw_ladders():
    for ladder in ladders:
        pygame.draw.rect(screen, BROWN, ladder)
        for y in range(ladder.top + 10, ladder.bottom, 25):
            pygame.draw.line(screen, BLACK, (ladder.left + 5, y), (ladder.right - 5, y), 3)

def draw_menu():
    screen.fill(WHITE)
    title = font.render("Stickman Jump", True, BLACK)
    screen.blit(title, (WIDTH//2-title.get_width()//2, 75))
    info = small_font.render(f"Mince: {total_coins}   Totem: {'koupen' if upgrades['totem'] else 'ne'}", True, BLACK)
    screen.blit(info, (WIDTH//2-info.get_width()//2, 160))
    for rect, text, color in [(start_button,"START",BLUE),(shop_button,"SHOP",PURPLE),(leaderboard_button,"LEADERBOARD",ORANGE)]:
        pygame.draw.rect(screen, color, rect)
        t = small_font.render(text, True, WHITE)
        screen.blit(t, (rect.centerx-t.get_width()//2, rect.y+16))
    controls = tiny_font.render("A/D nebo šipky = pohyb | SPACE = skok | W/↑ = žebřík | F = střelba | P = pauza", True, BLACK)
    screen.blit(controls, (WIDTH//2-controls.get_width()//2, 535))

def draw_upgrade_button(name, label, desc, effect):
    rect = shop_buttons[name]
    price = get_upgrade_price(name)
    color = GRAY if price is None else (GREEN if total_coins >= price else RED)
    pygame.draw.rect(screen, color, rect)
    price_text = "MAX" if price is None else f"{price} mincí"
    t = tiny_font.render(f"{label} | lvl {upgrades[name]} | {desc} | Cena: {price_text} | {effect}", True, WHITE)
    screen.blit(t, (rect.x + 15, rect.y + 14))

def draw_shop():
    screen.fill((235,235,245))
    title = font.render("SHOP", True, BLACK)
    screen.blit(title, (WIDTH//2-title.get_width()//2, 55))
    c = small_font.render(f"Mince: {total_coins}", True, BLACK)
    screen.blit(c, (WIDTH//2-c.get_width()//2, 120))
    pygame.draw.rect(screen, RED, back_button)
    bt = small_font.render("ZPĚT", True, WHITE)
    screen.blit(bt, (back_button.centerx-bt.get_width()//2, back_button.y+14))

    draw_upgrade_button("speed","Rychlost","rychlejší pohyb",f"{get_speed():.1f}")
    draw_upgrade_button("jump","Skok","vyšší skok",f"{abs(get_jump_power()):.1f}")
    draw_upgrade_button("weapon","Zbraň","odemkne F","aktivní" if upgrades["weapon"] else "zamčeno")
    draw_upgrade_button("fire_rate","Fire rate","rychlejší střelba",f"cooldown {get_fire_cooldown()}")
    draw_upgrade_button("shield","Štít","delší trvání",f"{get_shield_time()//60}s")
    draw_upgrade_button("max_lives","Životy","start 2, max 10",f"start {get_start_lives()}/10")
    draw_upgrade_button(
        "coin_spawn",
        "Coiny",
        "vyšší šance a víc mincí",
        f"šance {int(get_coin_spawn_chance() * 100)}%, počet random"
    )
    draw_upgrade_button("totem","Totem nesmrtelnosti","zachrání před lávou","nejdražší")

def draw_leaderboard():
    screen.fill((235,235,245))
    title = font.render("LEADERBOARD", True, BLACK)
    screen.blit(title, (WIDTH//2-title.get_width()//2, 70))
    pygame.draw.rect(screen, RED, back_button)
    bt = small_font.render("ZPĚT", True, WHITE)
    screen.blit(bt, (back_button.centerx-bt.get_width()//2, back_button.y+14))
    stats = [f"Nejvyšší skóre: {high_score}", f"Celkové mince: {total_coins}",
             f"Celkové killy: {total_kills}", f"Nejvíc killů v runu: {best_kills}",
             f"Počet smrtí: {total_deaths}", f"Odehrané runy: {runs_played}"]
    y = 210
    for s in stats:
        t = small_font.render(s, True, BLACK)
        screen.blit(t, (WIDTH//2-t.get_width()//2, y))
        y += 55

def draw_game():
    draw_background()
    draw_ladders()
    for p in platforms:
        if not p["visible"]:
            continue
        color = ICE_BLUE if p["type"] == "ice" else GHOST_GRAY if p["type"] == "disappearing" else PURPLE if p["moving"] else GREEN
        pygame.draw.rect(screen, color, p["rect"])
        if p["type"] == "ice":
            pygame.draw.line(screen, WHITE, (p["rect"].left+10, p["rect"].centery), (p["rect"].right-10, p["rect"].centery), 3)
        if p["type"] == "disappearing" and p["disappear_timer"] > 240:
            pygame.draw.rect(screen, RED, p["rect"], 4)

    for coin in coins: pygame.draw.ellipse(screen, YELLOW, coin)
    for shield in shield_powerups:
        pygame.draw.ellipse(screen, CYAN, shield)
        pygame.draw.circle(screen, WHITE, shield.center, 12, 3)
    for e in enemies:
        pygame.draw.ellipse(screen, PINK, e["rect"]) if e["type"] == "flying" else pygame.draw.rect(screen, RED, e["rect"])
    for b in enemy_bullets: pygame.draw.rect(screen, BLACK, b["rect"])
    for b in player_bullets: pygame.draw.rect(screen, BLUE, b["rect"])
    for ex in explosions: pygame.draw.circle(screen, ORANGE, (ex["x"], ex["y"]), ex["radius"], 3)

    draw_lava()

    frame = run_frames[int(frame_index)]
    if not facing_right:
        frame = pygame.transform.flip(frame, True, False)
    if not (invincible_timer > 0 and invincible_timer % 10 < 5):
        screen.blit(frame, (player.x - (SPRITE_SIZE-player.width)//2, player.y - (SPRITE_SIZE-player.height)))
    if shield_timer > 0:
        pygame.draw.circle(screen, CYAN, player.center, 55, 4)

    hud = [
        f"Skóre: {score}", f"Nejvyšší: {high_score}", f"Run mince: {coins_collected}",
        f"Celkem mince: {total_coins}", f"Killy: {kills}", f"Životy: {lives}",
        f"Totem: {totems_available}", f"Rychlost: {get_speed():.1f}", f"Skok: {abs(get_jump_power()):.1f}"
    ]
    y = 10
    for h in hud:
        t = tiny_font.render(h, True, BLACK)
        screen.blit(t, (10, y))
        y += 28
    if shield_timer > 0:
        screen.blit(tiny_font.render(f"Štít: {shield_timer//60+1}s", True, CYAN), (10, y))
    if paused:
        t = font.render("PAUZA", True, BLACK)
        screen.blit(t, (WIDTH//2-t.get_width()//2, HEIGHT//2-50))

def draw_game_over():
    screen.fill((30,30,30))
    lines = [("GAME OVER", font, RED), (f"Skóre: {score}", small_font, WHITE),
             (f"Killy: {kills}", small_font, WHITE), (f"Nejvyšší skóre: {high_score}", font, YELLOW),
             (f"Mince v runu: {coins_collected}", small_font, WHITE), (f"Celkové mince: {total_coins}", small_font, WHITE)]
    ys = [80,175,220,275,365,410]
    for (txt, fnt, col), y in zip(lines, ys):
        t = fnt.render(txt, True, col)
        screen.blit(t, (WIDTH//2-t.get_width()//2, y))
    for rect, txt, col in [(restart_button,"HRÁT ZNOVU",BLUE),(game_over_menu_button,"MENU",PURPLE)]:
        pygame.draw.rect(screen, col, rect)
        t = small_font.render(txt, True, WHITE)
        screen.blit(t, (rect.centerx-t.get_width()//2, rect.y+18))

def scroll_world(amount):
    global bg_x
    for group in [platforms, enemies]:
        for obj in group:
            obj["rect"].x -= amount
    for group in [coins, shield_powerups, ladders]:
        for obj in group:
            obj.x -= amount
    for group in [enemy_bullets, player_bullets]:
        for obj in group:
            obj["rect"].x -= amount
    bg_x -= bg_scroll_speed
    if bg_x <= -WIDTH:
        bg_x = 0

def teleport_to_safe_platform():
    global player_vel_y, shield_timer, invincible_timer
    visible = [p for p in platforms if p["visible"] and p["rect"].right > 0 and p["rect"].left < WIDTH]
    if not visible:
        return False
    nearest = min(visible, key=lambda p: abs(p["rect"].centerx - player.centerx) + abs(p["rect"].y - player.y))
    player.midbottom = (nearest["rect"].centerx, nearest["rect"].top)
    player_vel_y = 0
    shield_timer = 180
    invincible_timer = 120
    create_explosion(player.centerx, player.centery)
    return True

def instant_game_over():
    global game_state, high_score, total_deaths, best_kills, runs_played
    total_deaths += 1
    runs_played += 1
    high_score = max(high_score, score)
    best_kills = max(best_kills, kills)
    game_state = "game_over"

def lava_hit():
    global totems_available
    if totems_available > 0:
        totems_available -= 1
        if teleport_to_safe_platform():
            return
    instant_game_over()

def damage_player():
    global lives, invincible_timer, player_vel_y
    if shield_timer > 0 or invincible_timer > 0:
        return
    lives -= 1
    invincible_timer = 90
    player_vel_y = -10
    if lives <= 0:
        instant_game_over()

def update_moving_platforms():
    for p in platforms:
        if p["moving"] and p["visible"]:
            move = p["move_speed"] * p["move_dir"]
            p["rect"].x += move
            p["move_offset"] += move
            if abs(p["move_offset"]) >= p["move_range"]:
                p["move_dir"] *= -1

def update_disappearing_platforms():
    for p in platforms:
        if p["type"] == "disappearing":
            p["disappear_timer"] += 1
            p["visible"] = p["disappear_timer"] < 300
            if p["disappear_timer"] >= 600:
                p["disappear_timer"] = 0
                p["visible"] = True

def update_enemies():
    for e in enemies:
        if e["type"] == "ground":
            e["rect"].x += e["speed"]
            if e["rect"].left <= e["platform"].left or e["rect"].right >= e["platform"].right:
                e["speed"] *= -1
        else:
            e["rect"].y += e["move_speed"] * e["move_dir"]
            e["move_offset"] += e["move_speed"] * e["move_dir"]
            if abs(e["move_offset"]) >= e["move_range"]:
                e["move_dir"] *= -1
            e["shoot_timer"] -= 1
            if e["shoot_timer"] <= 0:
                if -100 < e["rect"].x < WIDTH + 100:
                    shoot_enemy_bullet(e)
                e["shoot_timer"] = random.randint(75, 150)

def update_bullets():
    for b in enemy_bullets[:]:
        b["rect"].x += b["speed"]
        if b["rect"].right < -100:
            enemy_bullets.remove(b)
    for b in player_bullets[:]:
        b["rect"].x += b["speed"]
        if b["rect"].left > WIDTH + 100 or b["rect"].right < -100:
            player_bullets.remove(b)

def update_explosions():
    for ex in explosions[:]:
        ex["timer"] -= 1
        ex["radius"] += 3
        if ex["timer"] <= 0:
            explosions.remove(ex)

def reset_run_variables():
    global player, platforms, coins, enemies, enemy_bullets, player_bullets, explosions
    global shield_powerups, ladders, last_main_platform, score, coins_collected, kills
    global lives, invincible_timer, bonus_life_coins, shield_timer, player_vel_y
    global coyote_timer, jump_buffer, paused, totems_available
    (player, platforms, coins, enemies, enemy_bullets, player_bullets, explosions,
     shield_powerups, ladders, last_main_platform, score, coins_collected, kills,
     lives, invincible_timer, bonus_life_coins, shield_timer, totems_available) = reset_game()
    player_vel_y = 0
    coyote_timer = 0
    jump_buffer = 0
    paused = False

running = True
while running:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if game_state == "menu" and event.type == pygame.MOUSEBUTTONDOWN:
            if start_button.collidepoint(event.pos):
                reset_run_variables()
                game_state = "game"
            elif shop_button.collidepoint(event.pos):
                game_state = "shop"
            elif leaderboard_button.collidepoint(event.pos):
                game_state = "leaderboard"

        elif game_state == "shop" and event.type == pygame.MOUSEBUTTONDOWN:
            if back_button.collidepoint(event.pos):
                game_state = "menu"
            for name, rect in shop_buttons.items():
                if rect.collidepoint(event.pos):
                    buy_upgrade(name)

        elif game_state == "leaderboard" and event.type == pygame.MOUSEBUTTONDOWN:
            if back_button.collidepoint(event.pos):
                game_state = "menu"

        elif game_state == "game" and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                paused = not paused
            if event.key == pygame.K_SPACE:
                jump_buffer = jump_buffer_max
            if event.key == pygame.K_f:
                shoot_player_bullet()

        elif game_state == "game_over" and event.type == pygame.MOUSEBUTTONDOWN:
            if restart_button.collidepoint(event.pos):
                reset_run_variables()
                game_state = "game"
            elif game_over_menu_button.collidepoint(event.pos):
                game_state = "menu"

    if game_state == "menu":
        draw_menu()

    elif game_state == "shop":
        draw_shop()

    elif game_state == "leaderboard":
        draw_leaderboard()

    elif game_state == "game":
        if not paused:
            keys = pygame.key.get_pressed()
            moving = False
            is_climbing = False
            standing_on_ice = False
            player_move_speed = get_speed()
            jump_power = get_jump_power()

            on_ladder = any(player.colliderect(lad) for lad in ladders)
            if on_ladder and (keys[pygame.K_w] or keys[pygame.K_UP]):
                is_climbing = True
                player.y -= 5
                player_vel_y = 0
            if on_ladder and (keys[pygame.K_s] or keys[pygame.K_DOWN]):
                is_climbing = True
                player.y += 5
                player_vel_y = 0

            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                moving = True
                facing_right = True
                if player.x < 280:
                    player.x += player_move_speed
                else:
                    scroll_world(scroll_speed)

            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                moving = True
                facing_right = False
                player.x -= player_move_speed
                if player.x < 50:
                    player.x = 50

            if jump_buffer > 0:
                jump_buffer -= 1
            if on_ground:
                coyote_timer = coyote_time_max
            else:
                coyote_timer -= 1
            if jump_buffer > 0 and coyote_timer > 0:
                player_vel_y = jump_power
                on_ground = False
                coyote_timer = 0
                jump_buffer = 0

            if not is_climbing:
                player_vel_y += gravity
                player.y += player_vel_y

            if player.top < 0:
                player.top = 0
                player_vel_y = 0

            if invincible_timer > 0: invincible_timer -= 1
            if shield_timer > 0: shield_timer -= 1
            if player_fire_timer > 0: player_fire_timer -= 1

            update_moving_platforms()
            update_disappearing_platforms()
            update_enemies()
            update_bullets()
            update_explosions()

            on_ground = False
            for p in platforms:
                if not p["visible"]:
                    continue
                if player.colliderect(p["rect"]) and player_vel_y > 0:
                    player.bottom = p["rect"].top
                    player_vel_y = 0
                    on_ground = True
                    if p["moving"]:
                        player.x += p["move_speed"] * p["move_dir"]
                    if p["type"] == "ice":
                        standing_on_ice = True
                        player.x += 3 if facing_right else -3
                        if player.x < 50: player.x = 50
                    if not p["scored"]:
                        p["scored"] = True
                        score += 1

            if standing_on_ice and not (keys[pygame.K_LEFT] or keys[pygame.K_a] or keys[pygame.K_RIGHT] or keys[pygame.K_d]):
                player.x += 2 if facing_right else -2
                if player.x < 50:
                    player.x = 50

            if player.bottom >= lava_rect.top:
                lava_hit()

            for b in player_bullets[:]:
                for e in enemies[:]:
                    if b["rect"].colliderect(e["rect"]):
                        create_explosion(e["rect"].centerx, e["rect"].centery)
                        if b in player_bullets: player_bullets.remove(b)
                        if e in enemies: enemies.remove(e)
                        kills += 1
                        total_kills += 1
                        score += 1
                        break

            for pb in player_bullets[:]:
                for eb in enemy_bullets[:]:
                    if pb["rect"].colliderect(eb["rect"]):
                        create_explosion(eb["rect"].centerx, eb["rect"].centery)
                        if pb in player_bullets: player_bullets.remove(pb)
                        if eb in enemy_bullets: enemy_bullets.remove(eb)
                        break

            for e in enemies[:]:
                if player.colliderect(e["rect"]):
                    if shield_timer > 0:
                        create_explosion(e["rect"].centerx, e["rect"].centery)
                        enemies.remove(e)
                        kills += 1
                        total_kills += 1
                        score += 1
                    else:
                        damage_player()
                        player.y = e["rect"].top - player.height

            for b in enemy_bullets[:]:
                if player.colliderect(b["rect"]):
                    if shield_timer > 0:
                        create_explosion(b["rect"].centerx, b["rect"].centery)
                    else:
                        damage_player()
                    enemy_bullets.remove(b)

            for coin in coins[:]:
                if player.colliderect(coin):
                    coins.remove(coin)
                    coins_collected += 1
                    total_coins += 1
                    bonus_life_coins += 1
                    if bonus_life_coins >= 10:
                        bonus_life_coins = 0
                        lives = min(10, lives + 1)

            for shield in shield_powerups[:]:
                if player.colliderect(shield):
                    shield_powerups.remove(shield)
                    shield_timer = get_shield_time()

            for p in platforms[:]:
                if p["rect"].right < -200:
                    platforms.remove(p)
            for group in [enemies, enemy_bullets, player_bullets]:
                for obj in group[:]:
                    if obj["rect"].right < -200:
                        group.remove(obj)
            for group in [coins, shield_powerups, ladders]:
                for obj in group[:]:
                    if obj.right < -200:
                        group.remove(obj)

            while last_main_platform["rect"].right < WIDTH + 350:
                generate_next_platform()

            if moving:
                frame_index += animation_speed
                if frame_index >= len(run_frames):
                    frame_index = 0
            else:
                frame_index = 0

        draw_game()

    elif game_state == "game_over":
        draw_game_over()

    pygame.display.flip()

pygame.quit()
sys.exit()
