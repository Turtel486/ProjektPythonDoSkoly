import pygame
import sys
import random

pygame.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Stickman Jump")

clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 70)
small_font = pygame.font.SysFont(None, 40)

# === NAHRAJ SI SVŮJ OBRÁZEK ===
background = pygame.image.load("stickman1.jpg").convert()
background = pygame.transform.scale(background, (WIDTH, HEIGHT))

bg_x = 0
bg_scroll_speed = 2

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (50, 150, 255)
GREEN = (50, 200, 50)
YELLOW = (255, 215, 0)

def reset_game():
    player = pygame.Rect(200, 500, 40, 40)

    platforms = [
        pygame.Rect(0, 550, 800, 50),
        pygame.Rect(350, 470, 140, 20),
        pygame.Rect(550, 400, 140, 20),
    ]

    coins = []
    score = 0

    return player, platforms, coins, score

player, platforms, coins, score = reset_game()

player_vel_y = 0
gravity = 0.6
jump_power = -13
on_ground = False
scroll_speed = 5

game_state = "menu"

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
        pygame.draw.rect(screen, GREEN, platform)

    for coin in coins:
        pygame.draw.ellipse(screen, YELLOW, coin)

    pygame.draw.rect(screen, BLUE, player)

    score_text = small_font.render(f"Coins: {score}", True, BLACK)
    screen.blit(score_text, (10, 10))

def draw_game_over():
    screen.fill((30, 30, 30))

    text = font.render("GAME OVER", True, (255, 50, 50))
    screen.blit(text, (WIDTH//2 - text.get_width()//2, 200))

    score_text = small_font.render(f"Coins: {score}", True, WHITE)
    screen.blit(score_text, (WIDTH//2 - score_text.get_width()//2, 300))

    restart_text = small_font.render("Klikni pro restart", True, WHITE)
    screen.blit(restart_text, (WIDTH//2 - restart_text.get_width()//2, 350))


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
                    player, platforms, coins, score = reset_game()

        elif game_state == "game_over":
            if event.type == pygame.MOUSEBUTTONDOWN:
                player, platforms, coins, score = reset_game()
                game_state = "game"

    if game_state == "menu":
        start_button = draw_menu()

    elif game_state == "game":

        keys = pygame.key.get_pressed()

        # Pohyb doprava
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            for platform in platforms:
                platform.x -= scroll_speed
            for coin in coins:
                coin.x -= scroll_speed
            bg_x -= bg_scroll_speed

        # Pohyb doleva
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            for platform in platforms:
                platform.x += scroll_speed
            for coin in coins:
                coin.x += scroll_speed
            bg_x += bg_scroll_speed

        # Nekonečné pozadí
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

        # Kolize
        on_ground = False
        for platform in platforms:
            if player.colliderect(platform) and player_vel_y > 0:
                player.bottom = platform.top
                player_vel_y = 0
                on_ground = True

        # Game Over když spadneš
        if player.top > HEIGHT:
            game_state = "game_over"

        # Sbírání coinů
        for coin in coins[:]:
            if player.colliderect(coin):
                coins.remove(coin)
                score += 1

        # Mazání starých platforem
        for platform in platforms[:]:
            if platform.right < -200:
                platforms.remove(platform)

        # Generování nových platforem
        if platforms[-1].right < WIDTH - 150:
            new_width = random.randint(120, 180)
            new_x = platforms[-1].right + random.randint(80, 140)
            new_y = random.randint(300, 500)

            new_platform = pygame.Rect(new_x, new_y, new_width, 20)
            platforms.append(new_platform)

            if random.random() < 0.4:
                coin = pygame.Rect(
                    new_x + new_width//2 - 10,
                    new_y - 30,
                    20,
                    20
                )
                coins.append(coin)

        draw_game()

    elif game_state == "game_over":
        draw_game_over()

    pygame.display.flip()

pygame.quit()
sys.exit()