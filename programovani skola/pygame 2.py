import pygame
import sys
import random

pygame.init()

# ========================
# Okno a fonty
# ========================
WIDTH, HEIGHT = 1200, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Stickman Jump")

clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 70)
small_font = pygame.font.SysFont(None, 40)

# Pozadí
try:
    background = pygame.image.load("stickman1.jpg").convert()
    background = pygame.transform.scale(background, (WIDTH, HEIGHT))
except FileNotFoundError:
    background = pygame.Surface((WIDTH, HEIGHT))
    background.fill((135, 206, 235)) # Světle modrá obloha jako záloha

bg_x = 0
bg_scroll_speed = 2

# Barvy
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (50, 150, 255)
GREEN = (50, 200, 50)
YELLOW = (255, 215, 0)
RED = (200, 50, 50)

# =========================
# ANIMACE BĚHU
# =========================
run_frames = []
try:
    for i in range(1, 7):
        img = pygame.image.load(f"run{i}.png").convert_alpha()
        img = pygame.transform.scale(img, (600, 600))
        run_frames.append(img)
except FileNotFoundError:
    for i in range(1, 7):
        surf = pygame.Surface((600, 600), pygame.SRCALPHA)
        pygame.draw.rect(surf, BLUE, (250, 400, 100, 200))
        run_frames.append(surf)

frame_index = 0
animation_speed = 0.2
facing_right = True

# =========================
# Globální proměnné
# =========================
high_score = 0

# =========================
# Reset hry
# =========================
def reset_game():
    hitbox_width = 50
    hitbox_height = 100
    player = pygame.Rect(200, HEIGHT - hitbox_height - 50, hitbox_width, hitbox_height)

    platforms = [
        {"rect": pygame.Rect(0, HEIGHT - 50, WIDTH, 50), "scored": True},
        {"rect": pygame.Rect(400, HEIGHT - 250, 300, 40), "scored": False},
        {"rect": pygame.Rect(800, HEIGHT - 350, 300, 40), "scored": False},
        {"rect": pygame.Rect(1300, HEIGHT - 450, 300, 40), "scored": False},
    ]

    coins = []
    enemies = []
    score = 0             # Skóre za platformy
    coins_collected = 0   # Samostatné počítadlo mincí
    lives = 3

    return player, platforms, coins, enemies, score, coins_collected, lives

player, platforms, coins, enemies, score, coins_collected, lives = reset_game()

# Fyzika
player_vel_y = 0
gravity = 0.6
jump_power = -20
on_ground = False
scroll_speed = 10

game_state = "menu"

# =========================
# Funkce
# =========================
def draw_background():
    screen.blit(background, (bg_x, 0))
    screen.blit(background, (bg_x + WIDTH, 0))

def draw_menu():
    screen.fill(WHITE)
    title = font.render("Stickman Jump", True, BLACK)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 150))

    start_button = pygame.Rect(WIDTH//2 - 100, 300, 200, 70)
    pygame.draw.rect(screen, BLUE, start_button)
    text = small_font.render("START", True, WHITE)
    screen.blit(text, (start_button.x + 55, start_button.y + 20))
    return start_button

def draw_game():
    draw_background()
    for platform in platforms:
        pygame.draw.rect(screen, GREEN, platform["rect"])
    for coin in coins:
        pygame.draw.ellipse(screen, YELLOW, coin)
    for enemy in enemies:
        pygame.draw.rect(screen, RED, enemy["rect"])

    # Animace hráče
    current_frame = run_frames[int(frame_index)]
    if not facing_right:
        current_frame = pygame.transform.flip(current_frame, True, False)
    sprite_x = player.x - (600 - player.width)//2
    sprite_y = player.y - (600 - player.height)
    screen.blit(current_frame, (sprite_x, sprite_y))

    # Texty v levém horním rohu
    score_text = small_font.render(f"Skóre: {score}", True, BLACK)
    high_score_text = small_font.render(f"Nejvyšší: {high_score}", True, BLACK)
    coins_text = small_font.render(f"Mince: {coins_collected}", True, BLACK)
    lives_text = small_font.render(f"Životy: {lives}", True, RED)
    
    screen.blit(score_text, (10, 10))
    screen.blit(high_score_text, (10, 50))
    screen.blit(coins_text, (10, 90))
    screen.blit(lives_text, (10, 130))

def draw_game_over():
    screen.fill((30, 30, 30))
    text = font.render("GAME OVER", True, (255, 50, 50))
    screen.blit(text, (WIDTH//2 - text.get_width()//2, 150))
    
    score_text = small_font.render(f"Skóre (platformy): {score}", True, WHITE)
    screen.blit(score_text, (WIDTH//2 - score_text.get_width()//2, 250))
    
    best_score_text = font.render(f"Nejvyšší skóre: {high_score}", True, YELLOW)
    screen.blit(best_score_text, (WIDTH//2 - best_score_text.get_width()//2, 300))

    coins_text = small_font.render(f"Nasbírané mince: {coins_collected}", True, WHITE)
    screen.blit(coins_text, (WIDTH//2 - coins_text.get_width()//2, 380))

    restart_text = small_font.render("Klikni pro restart", True, WHITE)
    screen.blit(restart_text, (WIDTH//2 - restart_text.get_width()//2, 480))

def spawn_enemy(platform_rect):
    enemy_width = 50
    enemy_height = 50
    enemy_x = random.randint(platform_rect.x, platform_rect.x + platform_rect.width - enemy_width)
    enemy_y = platform_rect.y - enemy_height
    speed = random.choice([-2, 2])
    return {"rect": pygame.Rect(enemy_x, enemy_y, enemy_width, enemy_height),
            "speed": speed,
            "platform": platform_rect}

# =========================
# Hlavní smyčka
# =========================
running = True
while running:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if game_state == "menu":
            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_button.collidepoint(event.pos):
                    game_state = "game"
                    player, platforms, coins, enemies, score, coins_collected, lives = reset_game()

        elif game_state == "game_over":
            if event.type == pygame.MOUSEBUTTONDOWN:
                player, platforms, coins, enemies, score, coins_collected, lives = reset_game()
                game_state = "game"

    if game_state == "menu":
        start_button = draw_menu()

    elif game_state == "game":
        keys = pygame.key.get_pressed()
        moving = False

        # Pohyb hráče + scroll světa
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            moving = True
            facing_right = True
            for platform in platforms[1:]:
                platform["rect"].x -= scroll_speed
            for coin in coins:
                coin.x -= scroll_speed
            for enemy in enemies:
                enemy["rect"].x -= scroll_speed
            bg_x -= bg_scroll_speed

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            moving = True
            facing_right = False
            for platform in platforms[1:]:
                platform["rect"].x += scroll_speed
            for coin in coins:
                coin.x += scroll_speed
            for enemy in enemies:
                enemy["rect"].x += scroll_speed
            bg_x += bg_scroll_speed

        if bg_x <= -WIDTH:
            bg_x = 0
        if bg_x >= WIDTH:
            bg_x = 0

        # Skok
        if keys[pygame.K_SPACE] and on_ground:
            player_vel_y = jump_power
            on_ground = False

        # Gravitace
        player_vel_y += gravity
        player.y += player_vel_y

        # Kolize s platformami
        on_ground = False
        for platform in platforms:
            if player.colliderect(platform["rect"]) and player_vel_y > 0:
                player.bottom = platform["rect"].top
                player_vel_y = 0
                on_ground = True
                
                # Zisk bodu za novou platformu
                if not platform["scored"]:
                    platform["scored"] = True
                    score += 1

        # Kolize s nepřáteli
        for enemy in enemies[:]:
            if player.colliderect(enemy["rect"]):
                lives -= 1
                player.y = enemy["rect"].top - player.height
                if lives <= 0:
                    if score > high_score:
                        high_score = score
                    game_state = "game_over"

        # Pád mimo obrazovku
        if player.top > HEIGHT:
            lives -= 1
            if lives <= 0:
                if score > high_score:
                    high_score = score
                game_state = "game_over"
            else:
                player.y = HEIGHT - player.height - 50
                player_vel_y = 0

        # Sbírání mincí
        for coin in coins[:]:
            if player.colliderect(coin):
                coins.remove(coin)
                coins_collected += 1  # Přičte se pouze do samostatného počítadla mincí

        # Mazání objektů mimo obrazovku
        for platform in platforms[1:]:
            if platform["rect"].right < -200:
                platforms.remove(platform)
        for enemy in enemies[:]:
            if enemy["rect"].right < -200 or enemy["rect"].left > WIDTH + 200:
                enemies.remove(enemy)

        # Generování nového obsahu
        if platforms[-1]["rect"].right < WIDTH - 200:
            new_width = random.randint(200, 400)
            new_x = platforms[-1]["rect"].right + random.randint(200, 400)
            new_y = random.randint(400, HEIGHT - 200)
            
            new_platform_rect = pygame.Rect(new_x, new_y, new_width, 40)
            platforms.append({"rect": new_platform_rect, "scored": False})
            
            if random.random() < 0.4:
                coin = pygame.Rect(new_x + new_width//2 - 20, new_y - 50, 40, 40)
                coins.append(coin)
            if random.random() < 0.5:
                enemies.append(spawn_enemy(new_platform_rect))

        # Pohyb nepřátel
        for enemy in enemies:
            enemy["rect"].x += enemy["speed"]
            if enemy["rect"].left <= enemy["platform"].left or enemy["rect"].right >= enemy["platform"].right:
                enemy["speed"] *= -1

        # Animace
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
