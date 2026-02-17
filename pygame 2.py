# Import knihoven pro hru, ukončení programu a náhodné generování
import pygame
import sys
import random

# Inicializace pygame – nutné pro spuštění všech funkcí
pygame.init()

# Nastavení velikosti okna
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Stickman Jump")  # Název okna

# Hodiny pro řízení FPS + fonty pro text
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 70)
small_font = pygame.font.SysFont(None, 40)

# Načtení pozadí
# Obrázek se načte a roztáhne na velikost obrazovky
background = pygame.image.load("stickman1.jpg").convert()
background = pygame.transform.scale(background, (WIDTH, HEIGHT))

# Proměnné pro posun pozadí
bg_x = 0
bg_scroll_speed = 2

# Definice barev (RGB)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (50, 150, 255)
GREEN = (50, 200, 50)
YELLOW = (255, 215, 0)

# Funkce pro resetování hry
def reset_game():
    # Vytvoření hráče (obdélník)
    player = pygame.Rect(200, 500, 40, 40)

    # Počáteční platformy
    platforms = [
        pygame.Rect(0, 550, 800, 50),
        pygame.Rect(350, 470, 140, 20),
        pygame.Rect(550, 400, 140, 20),
    ]

    # Mince a skóre
    coins = []
    score = 0

    return player, platforms, coins, score

# Zavolání resetu při startu
player, platforms, coins, score = reset_game()

# Fyzika hráče
player_vel_y = 0   # Vertikální rychlost
gravity = 0.6      # Síla gravitace
jump_power = -13   # Síla skoku
on_ground = False  # Kontrola zda hráč stojí
scroll_speed = 5   # Rychlost posunu světa

# Stav hry (menu / hra / game over)
game_state = "menu"

# Funkce pro vykreslení posouvajícího se pozadí
def draw_background():
    screen.blit(background, (bg_x, 0))
    screen.blit(background, (bg_x + WIDTH, 0))

# Funkce pro vykreslení menu
def draw_menu():
    screen.fill(WHITE)

    # Titulek
    title = font.render("Stickman Jump", True, BLACK)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 150))

    # Tlačítko START
    start_button = pygame.Rect(WIDTH//2 - 100, 300, 200, 70)
    pygame.draw.rect(screen, BLUE, start_button)

    text = small_font.render("START", True, WHITE)
    screen.blit(text, (start_button.x + 55, start_button.y + 20))

    return start_button

# Funkce pro vykreslení hry
def draw_game():
    draw_background()

    # Platformy
    for platform in platforms:
        pygame.draw.rect(screen, GREEN, platform)

    # Mince
    for coin in coins:
        pygame.draw.ellipse(screen, YELLOW, coin)

    # Hráč
    pygame.draw.rect(screen, BLUE, player)

    # Skóre
    score_text = small_font.render(f"Coins: {score}", True, BLACK)
    screen.blit(score_text, (10, 10))

# Funkce pro obrazovku GAME OVER
def draw_game_over():
    screen.fill((30, 30, 30))

    text = font.render("GAME OVER", True, (255, 50, 50))
    screen.blit(text, (WIDTH//2 - text.get_width()//2, 200))

    score_text = small_font.render(f"Coins: {score}", True, WHITE)
    screen.blit(score_text, (WIDTH//2 - score_text.get_width()//2, 300))

    restart_text = small_font.render("Klikni pro restart", True, WHITE)
    screen.blit(restart_text, (WIDTH//2 - restart_text.get_width()//2, 350))

# Hlavní herní smyčka
running = True
while running:
    clock.tick(60)  # Omezení na 60 FPS

    # Zpracování událostí
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Menu kliknutí
        if game_state == "menu":
            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_button.collidepoint(event.pos):
                    game_state = "game"
                    player, platforms, coins, score = reset_game()

        # Restart po game over
        elif game_state == "game_over":
            if event.type == pygame.MOUSEBUTTONDOWN:
                player, platforms, coins, score = reset_game()
                game_state = "game"

    # MENU stav
    if game_state == "menu":
        start_button = draw_menu()

    # HERNÍ stav
    elif game_state == "game":

        keys = pygame.key.get_pressed()

        # Pohyb doprava (svět se posouvá doleva)
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

        # Nekonečné scrollování pozadí
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
            if player.colliderect(platform) and player_vel_y > 0:
                player.bottom = platform.top
                player_vel_y = 0
                on_ground = True

        # Game over když hráč spadne
        if player.top > HEIGHT:
            game_state = "game_over"

        # Sbírání mincí
        for coin in coins[:]:
            if player.colliderect(coin):
                coins.remove(coin)
                score += 1

        # Mazání starých platforem
        for platform in platforms[:]:
            if platform.right < -200:
                platforms.remove(platform)

        # Generování nových platforem a mincí
        if platforms[-1].right < WIDTH - 150:
            new_width = random.randint(120, 180)
            new_x = platforms[-1].right + random.randint(80, 140)
            new_y = random.randint(300, 500)

            new_platform = pygame.Rect(new_x, new_y, new_width, 20)
            platforms.append(new_platform)

            # Náhodné vytvoření mince
            if random.random() < 0.4:
                coin = pygame.Rect(
                    new_x + new_width//2 - 10,
                    new_y - 30,
                    20,
                    20
                )
                coins.append(coin)

        draw_game()

    # GAME OVER stav
    elif game_state == "game_over":
        draw_game_over()

    # Aktualizace obrazovky
    pygame.display.flip()

# Ukončení hry
pygame.quit()
sys.exit()
