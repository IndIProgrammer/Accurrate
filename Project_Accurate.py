import pygame
import math
import random
import sys
import warnings
import json
import os
import numpy as np

warnings.filterwarnings("ignore", category=UserWarning, module="pkg_resources")

pygame.init()

# Константы
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.DOUBLEBUF)
pygame.display.set_caption("ACCURATE")
clock = pygame.time.Clock()

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
YELLOW = (255, 255, 0)
DARK_BLUE = (20, 20, 45)
GRAY = (100, 100, 120)
LIGHT_GRAY = (150, 150, 150)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
BLUE = (50, 100, 255)
CYAN = (0, 255, 255)

# Цвета для прицела
CROSSHAIR_COLORS = {
    "White": WHITE,
    "Red": RED,
    "Green": GREEN,
    "Blue": BLUE,
    "Yellow": YELLOW,
    "Cyan": CYAN
}

# Список доступных разрешений
RESOLUTIONS = {
    "2560x1440 (16:9 2K)": (2560, 1440),
    "2304x1440 (16:10 2K)": (2304, 1440),
    "1920x1440 (4:3 2K)": (1920, 1440),
    "1920x1080 (16:9 Full HD)": (1920, 1080),
    "1728x1080 (16:10 Full HD)": (1728, 1080),
    "1440x1080 (4:3 Full HD)": (1440, 1080),
    "1280x720 (16:9 HD)": (1280, 720),
    "1152x720 (16:10 HD)": (1152, 720),
    "960x720 (4:3 HD)": (960, 720)
}

# Предвычисленные значения для оптимизации
RAD_CONV = math.pi / 180
FOV = 90
FOV_RAD = FOV * RAD_CONV
SCALE_FACTOR = 1 / (2 * math.tan(FOV_RAD / 2))


# Возвращает путь к файлу настроек в AppData
def get_settings_path():
    if os.name == 'nt':
        appdata = os.getenv('APPDATA')
        if not appdata:
            appdata = os.path.expanduser('~')
        game_folder = os.path.join(appdata, 'Accurate')
    else:
        home = os.path.expanduser('~')
        game_folder = os.path.join(home, '.accurate')

    if not os.path.exists(game_folder):
        os.makedirs(game_folder)

    return os.path.join(game_folder, 'settings.json')

SETTINGS_FILE = get_settings_path()

# Загрузить настройки
def load_settings():
    default_settings = {
        "mouse_sensitivity": 0.25,
        "fullscreen": False,
        "volume": 0.5,
        "crosshair_color": "Red",
        "crosshair_size": 0.7,
        "show_grid": True,
        "fps_limit": 0,
        "resolution": "1920x1080 (16:9 Full HD)",
        "screen_width": 1920,
        "screen_height": 1080
    }

    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
                for key in default_settings:
                    if key not in settings:
                        settings[key] = default_settings[key]
                if "resolution" in settings and settings["resolution"] in RESOLUTIONS:
                    w, h = RESOLUTIONS[settings["resolution"]]
                    settings["screen_width"] = w
                    settings["screen_height"] = h
                return settings
        except:
            return default_settings
    return default_settings

# Сохраняет настройки в файл
def save_settings(settings):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=4)

# Загружаем настройки
settings = load_settings()

# Применяем настройки
if settings["fullscreen"]:
    screen = pygame.display.set_mode((settings["screen_width"], settings["screen_height"]),
                                     pygame.FULLSCREEN | pygame.DOUBLEBUF)
else:
    screen = pygame.display.set_mode((settings["screen_width"], settings["screen_height"]), pygame.DOUBLEBUF)

# Инициализация звука
pygame.mixer.init(frequency=44100, size=-16, channels=2)

# Создаём отдельные каналы для звуков
hit_channel = pygame.mixer.Channel(0)
shot_channel = pygame.mixer.Channel(1)

# Пытаемся загрузить звуки из файлов
try:
    shot_sound = None
    hit_sound = None

    if os.path.exists("shot.wav"):
        shot_sound = pygame.mixer.Sound("shot.wav")
        print("Загружен звук выстрела: shot.wav")
    elif os.path.exists("shot.wav"):
        shot_sound = pygame.mixer.Sound("shot.wav")
        print("Загружен звук выстрела: shot.wav")

    if os.path.exists("hit.wav"):
        hit_sound = pygame.mixer.Sound("hit.wav")
        print("Загружен звук попадания: hit.wav")
    elif os.path.exists("hit.wav"):
        hit_sound = pygame.mixer.Sound("hit.wav")
        print("Загружен звук попадания: hit.wav")

    # СИНТЕЗ ЗВУКА КОДОМ (Если внешние файлы не найдены)
    if shot_sound is None:
        sample_rate = 44100
        duration = 0.1
        samples = int(sample_rate * duration)
        arr = np.zeros(samples, dtype=np.int16)
        for i in range(samples):
            t = i / sample_rate
            # Линейное понижение частоты звука со временем (эффект выстрела)
            freq = 440 * (1 - t * 2)
            # Генерация синусоидальной волны с постепенным затуханием амплитуды (громкости)
            value = math.sin(2 * math.pi * freq * t) * (1 - t)
            value = max(-0.99, min(0.99, value))
            # Приведение дробного значения волны к 16-битному знаковому числу для аудиокарты
            arr[i] = int(value * 32767)
        stereo_arr = np.column_stack((arr, arr))  # Объединение моно-сигнала в стерео (два одинаковых канала)
        shot_sound = pygame.sndarray.make_sound(stereo_arr)

    if hit_sound is None:
        sample_rate = 44100
        duration = 0.15
        samples = int(sample_rate * duration)
        arr = np.zeros(samples, dtype=np.int16)
        for i in range(samples):
            t = i / sample_rate
            # Экспоненциальное (очень резкое) падение частоты для эффекта щелчка при попадании
            freq = 600 * math.exp(-t * 8)
            # Плавное затухание громкости по экспоненте
            value = math.sin(2 * math.pi * freq * t) * math.exp(-t * 10)
            value = max(-0.99, min(0.99, value))
            arr[i] = int(value * 32767)
        stereo_arr = np.column_stack((arr, arr))  # Конвертируем массив в стерео
        hit_sound = pygame.sndarray.make_sound(stereo_arr)

    if shot_sound:
        shot_sound.set_volume(settings["volume"])
    if hit_sound:
        hit_sound.set_volume(settings["volume"])

    print(f"Звуки готовы!")
except Exception as e:
    print(f"Ошибка загрузки звуков: {e}")
    shot_sound = None
    hit_sound = None

class Weapon:
    __slots__ = ('image', 'x', 'y', 'width', 'height', 'base_width')

    def __init__(self):
        self.image = None
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0
        self.base_width = 800  # Базовая ширина оружия в пикселях

        # Загружаем изображение автомата
        try:
            if os.path.exists("images/weapon.png"):
                self.image = pygame.image.load("images/weapon.png").convert_alpha()
                print("Загружен спрайт оружия: images/weapon.png")
            elif os.path.exists("weapon.png"):
                self.image = pygame.image.load("weapon.png").convert_alpha()
                print("Загружен спрайт оружия: weapon.png")

            if self.image:
                # Сохраняем оригинальные пропорции
                orig_width = self.image.get_width()
                orig_height = self.image.get_height()
                ratio = orig_height / orig_width

                # Устанавливаем желаемую ширину
                self.width = self.base_width
                self.height = int(self.width * ratio)
                self.image = pygame.transform.scale(self.image, (self.width, self.height))
        except Exception as e:
            print(f"Не удалось загрузить спрайт оружия: {e}")
            self.image = None

    def draw(self, screen, screen_width, screen_height):
        """Рисует оружие в правом нижнем углу"""
        if self.image:
            self.x = screen_width - self.width - 30
            self.y = screen_height - self.height - 30
            screen.blit(self.image, (self.x, self.y))

class Camera:
    __slots__ = ('x', 'y', 'z', 'yaw', 'pitch')

    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        self.yaw = 0
        self.pitch = 0

class Target:
    __slots__ = ('x', 'y', 'z', 'type')

    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        self.type = 'circle'

    # МАТЕМАТИЧЕСКАЯ ПРОЕКЦИЯ: Вычисление позиции 3D-мишени на плоском 2D-экране
    def get_screen_pos(self, cam, screen_width, screen_height):
        # Находим вектор смещения от положения камеры до мишени в мировых координатах
        dx = self.x - cam.x
        dy = self.y - cam.y
        dz = self.z - cam.z

        yaw_rad = cam.yaw * RAD_CONV
        cos_y = math.cos(yaw_rad)
        sin_y = math.sin(yaw_rad)

        # 1. ВРАЩЕНИЕ ВОКРУГ ОСИ Y (Влево-вправо / Yaw): пересчитываем X и Z с учетом поворота головы
        rotated_x = dx * cos_y + dz * sin_y
        rotated_z = dz * cos_y - dx * sin_y

        pitch_rad = cam.pitch * RAD_CONV
        cos_p = math.cos(pitch_rad)
        sin_p = math.sin(pitch_rad)

        # 2. ВРАЩЕНИЕ ВОКРУГ ОСИ X (Вверх-вниз / Pitch): пересчитываем Y и итоговую глубину Z
        rotated_y = dy * cos_p - rotated_z * sin_p
        final_z = rotated_z * cos_p + dy * sin_p  # Итоговое расстояние до объекта (глубина)

        # Если объект остался сзади игрока или вплотную к глазам — не проецируем его
        if final_z < 0.5:
            return None

        # 3. ФОРМУЛА ПЕРСПЕКТИВЫ: Деление на глубину (final_z) дает эффект объема.
        # Чем дальше мишень (больше final_z), тем сильнее её экранные x и y сдвигаются к центру экрана.
        scale = screen_height * SCALE_FACTOR
        screen_x = (rotated_x / final_z) * scale + screen_width * 0.5
        screen_y = (rotated_y / final_z) * scale + screen_height * 0.5

        # Динамическое масштабирование: размер круга на экране обратно пропорционален расстоянию до него
        size = int(32 * (5 / final_z))
        if size < 12:
            size = 12
        elif size > 65:
            size = 65

        return (int(screen_x), int(screen_y), size, final_z)

    # Отрисовка мишени
    def draw(self, screen, cam, screen_width, screen_height):
        pos = self.get_screen_pos(cam, screen_width, screen_height)
        if pos is None:
            return False

        x, y, size, _ = pos

        # Отрисовка концентрических кругов (мишени) на полученных 2D координатах
        pygame.draw.circle(screen, WHITE, (x, y), size)
        pygame.draw.circle(screen, BLACK, (x, y), size, 2)
        pygame.draw.circle(screen, RED, (x, y), size // 2)
        pygame.draw.circle(screen, BLACK, (x, y), size // 2, 1)

        return True

    # ПРОВЕРКА ПОПАДАНИЯ (Клик прицела по трехмерному объекту)
    def is_hit(self, cam, screen_width, screen_height):
        pos = self.get_screen_pos(cam, screen_width, screen_height)
        if pos is None:
            return False
        x, y, size, _ = pos
        cx, cy = screen_width // 2, screen_height // 2  # Точка прицела всегда в центре экрана

        # Расчет расстояния по теореме Пифагора (квадрат расстояния) между центром экрана и центром мишени
        dx = cx - x
        dy = cy - y
        return (dx * dx + dy * dy) <= size * size

# Отрисовка 3D пространства на 2D экране (используется для узлов сетки пола и потолка)
def world_to_screen(x, y, z, cam, screen_width, screen_height):
    dx = x - cam.x
    dy = y - cam.y
    dz = z - cam.z

    yaw_rad = cam.yaw * RAD_CONV
    cos_y = math.cos(yaw_rad)
    sin_y = math.sin(yaw_rad)

    # Матричный поворот точки вокруг вертикальной оси игрока (Yaw)
    rotated_x = dx * cos_y + dz * sin_y
    rotated_z = dz * cos_y - dx * sin_y

    pitch_rad = cam.pitch * RAD_CONV
    cos_p = math.cos(pitch_rad)
    sin_p = math.sin(pitch_rad)

    # Матричный поворот точки вокруг горизонтальной оси взгляда игрока (Pitch)
    rotated_y = dy * cos_p - rotated_z * sin_p
    final_z = rotated_z * cos_p + dy * sin_p

    if final_z < 0.5:
        return None

    # Проекция на плоскость экрана с учетом FOV и масштаба
    scale = screen_height * SCALE_FACTOR
    screen_x = (rotated_x / final_z) * scale + screen_width * 0.5
    screen_y = (rotated_y / final_z) * scale + screen_height * 0.5

    return (int(screen_x), int(screen_y))

# Отрисовка пола
def draw_floor(screen, cam, screen_width, screen_height):
    """Рисует пол с сеткой (оптимизированная)"""
    if not settings.get("show_grid", True):
        return

    current_w, current_h = screen.get_size()

    if current_w >= 1920:
        grid_size = 12
        cell_size = 2.5
        step = 2
    elif current_w >= 1280:
        grid_size = 10
        cell_size = 2.5
        step = 2
    else:
        grid_size = 8
        cell_size = 2.5
        step = 2

    for i in range(-grid_size, grid_size + 1, step):
        for j in range(-grid_size, grid_size + 1, step):
            p1 = (i * cell_size, 5.0, j * cell_size)
            p2 = ((i + step) * cell_size, 5.0, j * cell_size)
            p3 = (i * cell_size, 5.0, (j + step) * cell_size)

            s1 = world_to_screen(p1[0], p1[1], p1[2], cam, screen_width, screen_height)
            s2 = world_to_screen(p2[0], p2[1], p2[2], cam, screen_width, screen_height)
            s3 = world_to_screen(p3[0], p3[1], p3[2], cam, screen_width, screen_height)

            if s1 and s2:
                pygame.draw.line(screen, GRAY, s1, s2, 1)
            if s1 and s3:
                pygame.draw.line(screen, GRAY, s1, s3, 1)

# Отрисовка потолка
def draw_roof(screen, cam, screen_width, screen_height):
    """Рисует потолок с сеткой (оптимизированная)"""
    if not settings.get("show_grid", True):
        return

    current_w, current_h = screen.get_size()

    if current_w >= 1920:
        grid_size = 12
        cell_size = 2.5
        step = 2
    elif current_w >= 1280:
        grid_size = 10
        cell_size = 2.5
        step = 2
    else:
        grid_size = 8
        cell_size = 2.5
        step = 2

    for i in range(-grid_size, grid_size + 1, step):
        for j in range(-grid_size, grid_size + 1, step):
            p1 = (i * cell_size, -1.0, j * cell_size)
            p2 = ((i + step) * cell_size, -1.0, j * cell_size)
            p3 = (i * cell_size, -1.0, (j + step) * cell_size)

            s1 = world_to_screen(p1[0], p1[1], p1[2], cam, screen_width, screen_height)
            s2 = world_to_screen(p2[0], p2[1], p2[2], cam, screen_width, screen_height)
            s3 = world_to_screen(p3[0], p3[1], p3[2], cam, screen_width, screen_height)

            if s1 and s2:
                pygame.draw.line(screen, GRAY, s1, s2, 1)
            if s1 and s3:
                pygame.draw.line(screen, GRAY, s1, s3, 1)

# Отрисовка прицела
def draw_crosshair(screen, color, size_multiplier=1.0):
    current_w, current_h = screen.get_size()
    cx, cy = current_w // 2, current_h // 2

    base_outer_len = 22
    base_inner_len = 14
    base_gap = 10
    base_circle_radius = 3
    base_line_width = 2

    outer_len = int(base_outer_len * size_multiplier)
    inner_len = int(base_inner_len * size_multiplier)
    gap = int(base_gap * size_multiplier)
    circle_radius = max(1, int(base_circle_radius * size_multiplier))
    line_width = max(1, int(base_line_width * size_multiplier))

    if current_w < 1280:
        outer_len = int(outer_len * 0.8)
        inner_len = int(inner_len * 0.8)
        gap = int(gap * 0.8)
        circle_radius = max(1, int(circle_radius * 0.8))
        line_width = max(1, int(line_width * 0.8))

    pygame.draw.line(screen, color, (cx - outer_len, cy), (cx - gap, cy), line_width)
    pygame.draw.line(screen, color, (cx + outer_len, cy), (cx + gap, cy), line_width)
    pygame.draw.line(screen, color, (cx, cy - outer_len), (cx, cy - gap), line_width)
    pygame.draw.line(screen, color, (cx, cy + outer_len), (cx, cy + gap), line_width)

    inner_line_width = max(1, line_width - 1)
    pygame.draw.line(screen, WHITE, (cx - inner_len, cy), (cx - gap + 2, cy), inner_line_width)
    pygame.draw.line(screen, WHITE, (cx + inner_len, cy), (cx + gap - 2, cy), inner_line_width)
    pygame.draw.line(screen, WHITE, (cx, cy - inner_len), (cx, cy - gap + 2), inner_line_width)
    pygame.draw.line(screen, WHITE, (cx, cy + inner_len), (cx, cy + gap - 2), inner_line_width)

    pygame.draw.circle(screen, color, (cx, cy), circle_radius, line_width)

# Игровой цикл
def game_loop(mode='endless'):
    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)

    cam = Camera(0.0, 2.0, 0.0)

    # Создаём объект оружия
    weapon = Weapon()

    score = 0
    misses = 0
    shots_fired = 0
    has_hit = False # Флаг для пасхалки

    targets = []
    spawn_timer = 0

    start_time = pygame.time.get_ticks()
    time_limit = 60 * 1000

    font = pygame.font.Font(None, 36)
    small_font = pygame.font.Font(None, 24)

    running = True

    fps_limit = settings.get("fps_limit", 0)
    game_clock = pygame.time.Clock()

    while running:
        if fps_limit > 0:
            game_clock.tick(fps_limit)
        else:
            game_clock.tick()

        dt = game_clock.get_time() / 1000.0
        if dt > 0.033:
            dt = 0.033

        screen_width, screen_height = screen.get_size()

        if mode == 'timed':
            elapsed = pygame.time.get_ticks() - start_time
            remaining = max(0, time_limit - elapsed)
            if remaining <= 0:
                # Передаем флаг попадания в экран результатов
                return show_game_result(score, misses, shots_fired, mode, has_hit)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    shots_fired += 1

                    if shot_sound:
                        shot_channel.play(shot_sound)

                    hit_target = None
                    min_dist = float('inf')

                    # ПОИСК БЛИЖАЙШЕЙ МИШЕНИ ПРИ КЛИКЕ
                    # Если под перекрестие прицела попало несколько мишеней (одна за другой),
                    # код находит ту, у которой координата глубины Z (pos[3]) минимальна, чтобы засчитать клик по ближней.
                    for target in targets:
                        if target.is_hit(cam, screen_width, screen_height):
                            pos = target.get_screen_pos(cam, screen_width, screen_height)
                            if pos and pos[3] < min_dist:
                                min_dist = pos[3]
                                hit_target = target

                    if hit_target:
                        targets.remove(hit_target)
                        score += 1
                        has_hit = True # Отмечаем, что было попадание
                        if hit_sound:
                            hit_channel.play(hit_sound)
                    else:
                        misses += 1

        mouse_dx, mouse_dy = pygame.mouse.get_rel()
        cam.yaw -= mouse_dx * settings["mouse_sensitivity"]
        cam.pitch += mouse_dy * settings["mouse_sensitivity"]
        cam.pitch = max(-45, min(45, cam.pitch))

        # АЛГОРИТМ СТУПЕНЧАТОГО СПАВНА МИШЕНЕЙ С ПРОВЕРКОЙ НА НАЛОЖЕНИЕ (Overlap)
        spawn_timer += dt
        if spawn_timer > 0.5 and len(targets) < 10:
            spawn_timer = 0
            x = random.uniform(-5, 5)
            z = random.uniform(3, 9)
            y = random.uniform(0.5, 2.0)

            overlap = False
            # Проверяем Евклидово расстояние в 3D пространстве между новой точкой и всеми живыми мишенями.
            # Если расстояние меньше чем 1.5 метра (в квадрате < 2.25), спавн отменяется, чтобы они не слипались.
            for target in targets:
                dx = target.x - x
                dz = target.z - z
                dy = target.y - y
                if (dx * dx + dy * dy + dz * dz) < 2.25:
                    overlap = True
                    break

            if not overlap:
                targets.append(Target(x, y, z))

        screen.fill(DARK_BLUE)
        draw_floor(screen, cam, screen_width, screen_height)
        draw_roof(screen, cam, screen_width, screen_height)

        # АЛГОРИТМ ХУДОЖНИКА (Z-сортировка перед выводом на 2D экран)
        # Так как Pygame плоский, объекты рисуются последовательно. Создаем список пар (мишень, глубина).
        targets_with_dist = []
        for target in targets:
            pos = target.get_screen_pos(cam, screen_width, screen_height)
            if pos:
                targets_with_dist.append((target, pos[3]))

        # Сортируем список по убыванию расстояния (reverse=True).
        # Сначала нарисуются самые дальние мишени, а затем поверх них — ближние. Это исключает визуальные баги наложения.
        targets_with_dist.sort(key=lambda x: x[1], reverse=True)

        for target, _ in targets_with_dist:
            target.draw(screen, cam, screen_width, screen_height)

        crosshair_color = CROSSHAIR_COLORS.get(settings["crosshair_color"], RED)
        crosshair_size = settings.get("crosshair_size", 1.0)
        draw_crosshair(screen, crosshair_color, crosshair_size)

        accuracy = (score / shots_fired * 100) if shots_fired > 0 else 0

        text_surface = pygame.Surface((260, 180))
        text_surface.set_alpha(180)
        text_surface.fill(BLACK)
        screen.blit(text_surface, (10, 10))

        screen.blit(font.render(f"SCORE: {score}", True, YELLOW), (20, 20))
        screen.blit(small_font.render(f"MISSES: {misses}", True, RED), (20, 65))
        screen.blit(small_font.render(f"ACCURACY: {accuracy:.1f}%", True, GREEN), (20, 98))
        screen.blit(small_font.render(f"TARGETS: {len(targets)}", True, LIGHT_GRAY), (20, 128))

        if mode == 'timed':
            seconds_remaining = remaining // 1000
            time_text = small_font.render(f"TIME: {seconds_remaining}s", True, ORANGE)
            screen.blit(time_text, (20, 158))

        screen.blit(small_font.render(f"FPS: {int(game_clock.get_fps())}", True, LIGHT_GRAY), (20, screen_height - 40))

        controls = small_font.render("MOUSE: AIM | LMB: SHOOT | ESC: EXIT", True, GRAY)
        controls_rect = controls.get_rect(center=(screen_width // 2, screen_height - 20))
        screen.blit(controls, controls_rect)

        # Отрисовка оружия (поверх всего)
        weapon.draw(screen, screen_width, screen_height)

        pygame.display.flip()

    pygame.mouse.set_visible(True)
    pygame.event.set_grab(False)
    return

# Файл для сохранения статистики
STATS_FILE = os.path.join(os.path.dirname(SETTINGS_FILE), "stats.json")

# Загружает статистику игр (история лучших результатов)
def load_stats():
    default_stats = {
        "best_games": [],  # Список лучших игр (история рекордов)
        "total_shots": 0,
        "total_hits": 0,
        "total_misses": 0,
        "best_accuracy": 0,
        "best_score": 0,
        "games_played": 0
    }

    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, 'r') as f:
                stats = json.load(f)
                for key in default_stats:
                    if key not in stats:
                        stats[key] = default_stats[key]
                return stats
        except:
            return default_stats
    return default_stats

# Сохраняет статистику
def save_stats(stats):
    with open(STATS_FILE, 'w') as f:
        json.dump(stats, f, indent=4)

# Возвращает текущий лучший счёт для данного режима
def get_current_best_score(mode, stats):
    best_score = 0
    for game in stats["best_games"]:
        if game["mode"] == mode and game["score"] > best_score:
            best_score = game["score"]
    return best_score

# Добавляет результат игры, только если он лучше текущего лучшего
def add_game_result(mode, score, misses, shots_fired, accuracy):
    stats = load_stats()

    # Получаем текущий лучший счёт для этого режима
    current_best = get_current_best_score(mode, stats)

    # Если результат лучше текущего лучшего (или это первая игра в этом режиме)
    if score > current_best:
        # Создаём запись об игре
        game_record = {
            "date": pygame.time.get_ticks(),
            "mode": mode,
            "score": score,
            "misses": misses,
            "shots": shots_fired,
            "accuracy": accuracy
        }

        # Добавляем запись в историю
        stats["best_games"].append(game_record)

        # Сортируем по дате (новые сверху) и ограничиваем 50 записями
        stats["best_games"].sort(key=lambda x: x["date"], reverse=True)
        if len(stats["best_games"]) > 50:
            stats["best_games"] = stats["best_games"][:50]

    # Обновляем общую статистику (суммарную) - всё равно суммируем все игры
    stats["total_shots"] += shots_fired
    stats["total_hits"] += score
    stats["total_misses"] += misses
    stats["games_played"] += 1

    # Обновляем лучшие показатели (глобальные)
    if accuracy > stats["best_accuracy"]:
        stats["best_accuracy"] = accuracy
    if score > stats["best_score"]:
        stats["best_score"] = score

    save_stats(stats)

# Показывает статистику и историю лучших игр
def show_statistics():
    pygame.mouse.set_visible(True)
    pygame.event.set_grab(False)

    stats = load_stats()

    running = True
    scroll_offset = 0
    max_scroll = max(0, len(stats["best_games"]) - 8)

    while running:
        current_w, current_h = screen.get_size()

        if current_w >= 1920:
            font_title_size = 56
            font_header_size = 32
            font_text_size = 24
            font_small_size = 20
            line_height = 35
        elif current_w >= 1280:
            font_title_size = 48
            font_header_size = 28
            font_text_size = 20
            font_small_size = 18
            line_height = 30
        else:
            font_title_size = 36
            font_header_size = 24
            font_text_size = 18
            font_small_size = 16
            line_height = 25

        font_title = pygame.font.Font(None, font_title_size)
        font_header = pygame.font.Font(None, font_header_size)
        font_text = pygame.font.Font(None, font_text_size)
        font_small = pygame.font.Font(None, font_small_size)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_SPACE:
                    running = False
                elif event.key == pygame.K_UP or event.key == pygame.K_w:
                    scroll_offset = max(0, scroll_offset - 1)
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    scroll_offset = min(max_scroll, scroll_offset + 1)
            elif event.type == pygame.MOUSEWHEEL:
                scroll_offset = max(0, min(max_scroll, scroll_offset - event.y))

        screen.fill(DARK_BLUE)

        title = font_title.render("RECORDS HISTORY", True, YELLOW)
        title_rect = title.get_rect(center=(current_w // 2, 50))
        screen.blit(title, title_rect)

        total_accuracy = (stats["total_hits"] / stats["total_shots"] * 100) if stats["total_shots"] > 0 else 0

        stats_y = 120
        stats_texts = [
            f"Games Played: {stats['games_played']}",
            f"Total Shots: {stats['total_shots']}",
            f"Total Hits: {stats['total_hits']}",
            f"Total Misses: {stats['total_misses']}",
            f"Overall Accuracy: {total_accuracy:.1f}%",
            f"Best Accuracy: {stats['best_accuracy']:.1f}%",
            f"Best Score: {stats['best_score']}"
        ]

        stats_bg = pygame.Surface((current_w - 40, 180))
        stats_bg.set_alpha(150)
        stats_bg.fill(BLACK)
        screen.blit(stats_bg, (20, stats_y - 10))

        for i, text in enumerate(stats_texts):
            txt = font_text.render(text, True, WHITE)
            screen.blit(txt, (30, stats_y + i * 25))

        history_y = stats_y + 180
        history_header = font_header.render("BEST ACHIEVEMENTS", True, YELLOW)
        screen.blit(history_header, (30, history_y))

        headers = ["#", "Mode", "Score", "Misses", "Shots", "Accuracy"]
        header_x = [30, 100, 250, 350, 450, 550]

        if current_w < 1280:
            header_x = [30, 90, 200, 280, 360, 440]

        for i, header in enumerate(headers):
            txt = font_small.render(header, True, LIGHT_GRAY)
            screen.blit(txt, (header_x[i], history_y + 35))

        history_bg = pygame.Surface((current_w - 40, 350))
        history_bg.set_alpha(150)
        history_bg.fill(BLACK)
        screen.blit(history_bg, (20, history_y + 30))

        games = stats["best_games"]
        visible_games = games[scroll_offset:scroll_offset + 8]

        for i, game in enumerate(visible_games):
            y_pos = history_y + 65 + i * line_height
            if y_pos > current_h - 100:
                break

            num = scroll_offset + i + 1
            num_txt = font_small.render(str(num), True, WHITE)
            screen.blit(num_txt, (header_x[0], y_pos))

            mode_txt = font_small.render(game["mode"].capitalize(), True, CYAN if game["mode"] == "timed" else GREEN)
            screen.blit(mode_txt, (header_x[1], y_pos))

            score_txt = font_small.render(str(game["score"]), True, YELLOW)
            screen.blit(score_txt, (header_x[2], y_pos))

            misses_txt = font_small.render(str(game["misses"]), True, RED)
            screen.blit(misses_txt, (header_x[3], y_pos))

            shots_txt = font_small.render(str(game["shots"]), True, LIGHT_GRAY)
            screen.blit(shots_txt, (header_x[4], y_pos))

            acc_color = GREEN if game["accuracy"] >= 70 else (YELLOW if game["accuracy"] >= 50 else RED)
            acc_txt = font_small.render(f"{game['accuracy']:.1f}%", True, acc_color)
            screen.blit(acc_txt, (header_x[5], y_pos))

        if max_scroll > 0:
            scroll_percent = scroll_offset / max_scroll
            scroll_bar_height = 80
            scroll_bar_y = history_y + 40 + scroll_percent * (350 - scroll_bar_height)
            pygame.draw.rect(screen, GREEN, (current_w - 25, history_y + 40, 10, scroll_bar_height))
            pygame.draw.rect(screen, YELLOW, (current_w - 25, scroll_bar_y, 10, scroll_bar_height))

        controls = font_small.render("W/S or UP/DOWN: Scroll | Mouse Wheel: Scroll | ESC/SPACE: Back", True, GRAY)
        controls_rect = controls.get_rect(center=(current_w // 2, current_h - 40))
        screen.blit(controls, controls_rect)

        clear_btn = pygame.Rect(current_w - 150, current_h - 90, 130, 35)
        pygame.draw.rect(screen, RED, clear_btn, 2)
        clear_text = font_small.render("Clear History", True, RED)
        clear_text_rect = clear_text.get_rect(center=clear_btn.center)
        screen.blit(clear_text, clear_text_rect)

        mouse_pos = pygame.mouse.get_pos()
        mouse_click = pygame.mouse.get_pressed()
        if clear_btn.collidepoint(mouse_pos) and mouse_click[0]:
            stats = {
                "best_games": [],
                "total_shots": 0,
                "total_hits": 0,
                "total_misses": 0,
                "best_accuracy": 0,
                "best_score": 0,
                "games_played": 0
            }
            save_stats(stats)
            scroll_offset = 0
            max_scroll = 0

        pygame.display.flip()
        clock.tick(60)

# Результат игры
def show_game_result(score, misses, shots_fired, mode='endless', easter_egg=False):
    pygame.mouse.set_visible(True)
    pygame.event.set_grab(False)

    accuracy = (score / shots_fired * 100) if shots_fired > 0 else 0
    screen_width, screen_height = screen.get_size()

    add_game_result(mode, score, misses, shots_fired, accuracy)

    font_big = pygame.font.Font(None, 72)
    font = pygame.font.Font(None, 48)
    small_font = pygame.font.Font(None, 36)

    result = True
    while result:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    return
                elif event.key == pygame.K_ESCAPE:
                    return

        screen.fill(DARK_BLUE)

        title = font_big.render("TIME'S UP!" if mode == 'timed' else "GAME OVER", True, YELLOW)
        title_rect = title.get_rect(center=(screen_width // 2, 150))
        screen.blit(title, title_rect)

        score_text = font.render(f"Score: {score}", True, WHITE)
        score_rect = score_text.get_rect(center=(screen_width // 2, 280))
        screen.blit(score_text, score_rect)

        misses_text = font.render(f"Misses: {misses}", True, RED)
        misses_rect = misses_text.get_rect(center=(screen_width // 2, 350))
        screen.blit(misses_text, misses_rect)

        acc_text = font.render(f"Accuracy: {accuracy:.1f}%", True, GREEN)
        acc_rect = acc_text.get_rect(center=(screen_width // 2, 420))
        screen.blit(acc_text, acc_rect)

        if mode == 'timed' and easter_egg and score == 1:
            secret_font = pygame.font.Font(None, 32)
            egg_surface = secret_font.render("GREATEST AIM MASTER", True, CYAN)
            egg_rect = egg_surface.get_rect(center=(screen_width // 2, 480))
            screen.blit(egg_surface, egg_rect)

        continue_text = small_font.render("Press SPACE or ESC to continue", True, GRAY)
        continue_rect = continue_text.get_rect(center=(screen_width // 2, 550))
        screen.blit(continue_text, continue_rect)

        pygame.display.flip()
        clock.tick(60)

# Меню создателей
def show_creators():
    pygame.mouse.set_visible(True)
    pygame.event.set_grab(False)

    running = True
    while running:
        current_w, current_h = screen.get_size()

        if current_w >= 1920:
            font_big_size = 72
            font_small_size = 32
            line_height = 50
            title_y = int(current_h * 0.12)
            start_y = int(current_h * 0.25)
        elif current_w >= 1280:
            font_big_size = 56
            font_small_size = 28
            line_height = 45
            title_y = int(current_h * 0.12)
            start_y = int(current_h * 0.25)
        else:
            font_big_size = 40
            font_small_size = 20
            line_height = 35
            title_y = int(current_h * 0.1)
            start_y = int(current_h * 0.2)

        font_big = pygame.font.Font(None, font_big_size)
        small_font = pygame.font.Font(None, font_small_size)

        creators = [
            "Game Developers:",
            "",
            "Team Lead: Kirill Snigirev",
            "",
            "Programmer: Kirill Istushkin",
            "",
            "3D Graphics: Galichansky Matvey",
            "",
            "Design: Ryzhov Sergey",
            "",
            "Manager: Shlykov Mihail",
            "",
            "Special Thanks:",
            "All playtesters",
            "",
            "© 2026 Accurate"
        ]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_SPACE:
                    running = False

        screen.fill(DARK_BLUE)

        title = font_big.render("CREATORS", True, YELLOW)
        title_rect = title.get_rect(center=(current_w // 2, title_y))
        screen.blit(title, title_rect)

        text_surface = pygame.Surface((int(current_w * 0.7), int(current_h * 0.6)))
        text_surface.set_alpha(180)
        text_surface.fill(BLACK)
        text_surface_x = (current_w - text_surface.get_width()) // 2
        text_surface_y = start_y - 20
        screen.blit(text_surface, (text_surface_x, text_surface_y))

        y_offset = start_y
        for creator in creators:
            if creator == "":
                y_offset += line_height * 0.4
                continue
            text = small_font.render(creator, True, WHITE)
            text_rect = text.get_rect(center=(current_w // 2, y_offset))
            screen.blit(text, text_rect)
            y_offset += line_height

        continue_text = small_font.render("Press SPACE or ESC to return", True, GRAY)
        continue_rect = continue_text.get_rect(center=(current_w // 2, current_h - 50))
        screen.blit(continue_text, continue_rect)

        pygame.display.flip()
        clock.tick(60)

# Главное меню
def main_menu():
    pygame.mouse.set_visible(True)
    pygame.event.set_grab(False)

    menu_items = [
        "1. INFINITE MODE",
        "2. TIME MODE (60 sec)",
        "3. STATISTICS",
        "4. SETTINGS",
        "5. CREATORS",
        "6. EXIT"
    ]

    konami_code = [pygame.K_UP, pygame.K_UP, pygame.K_DOWN, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT, pygame.K_LEFT,
                   pygame.K_RIGHT, pygame.K_b, pygame.K_a]
    user_input = []

    selected = 0
    angle = 0
    preview_cam = Camera(0, 2, 0)

    keyboard_nav = True
    last_mouse_move = pygame.time.get_ticks()
    mouse_cooldown = 500

    # Флаги для диалога подтверждения
    confirm_exit = False
    confirm_selected = 0  # 0 = Yes, 1 = No
    exit_requested = False  # Флаг для запроса выхода через ESC

    disco_mode = False

    running = True
    while running:
        current_w, current_h = screen.get_size()

        if current_w >= 1920:
            font_title_size = 96
            font_subtitle_size = 52  # Увеличенный шрифт для Aim Trainer
            font_menu_size = 48
            font_info_size = 24
            font_confirm_size = 36
        elif current_w >= 1280:
            font_title_size = 72
            font_subtitle_size = 38  # Увеличенный шрифт для Aim Trainer
            font_menu_size = 36
            font_info_size = 20
            font_confirm_size = 28
        else:
            font_title_size = 48
            font_subtitle_size = 28  # Увеличенный шрифт для Aim Trainer
            font_menu_size = 28
            font_info_size = 16
            font_confirm_size = 24

        font_title = pygame.font.Font(None, font_title_size)
        font_subtitle = pygame.font.Font(None, font_subtitle_size)  # Отдельный шрифт для подзаголовка
        font_menu = pygame.font.Font(None, font_menu_size)
        font_info = pygame.font.Font(None, font_info_size)
        font_confirm = pygame.font.Font(None, font_confirm_size)

        title_y = int(current_h * 0.12)
        subtitle_y = int(current_h * 0.22)  # Немного сместим вниз
        menu_start_y = int(current_h * 0.32)  # Сместим меню вниз
        menu_step = int(current_h * 0.07)
        controls_y = int(current_h * 0.85)

        menu_surface_width = int(current_w * 0.6)
        menu_surface_height = int(current_h * 0.75)
        menu_surface_x = (current_w - menu_surface_width) // 2
        menu_surface_y = (current_h - menu_surface_height) // 2

        mouse_x, mouse_y = pygame.mouse.get_pos()
        current_time = pygame.time.get_ticks()

        # Вычисляем координаты кнопок диалога (если диалог активен)
        dialog_yes_btn = None
        dialog_no_btn = None
        if confirm_exit:
            dialog_width = 420
            dialog_height = 160
            dialog_x = (current_w - dialog_width) // 2
            dialog_y = (current_h - dialog_height) // 2
            dialog_yes_btn = pygame.Rect(dialog_x + 50, dialog_y + 90, 130, 40)
            dialog_no_btn = pygame.Rect(dialog_x + dialog_width - 180, dialog_y + 90, 130, 40)

        mouse_moved = False
        for event in pygame.event.get(pygame.MOUSEMOTION):
            mouse_moved = True
            last_mouse_move = current_time

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.type == pygame.KEYDOWN:
                    # Добавляем нажатую клавишу в наш список
                    user_input.append(event.key)

                    # Ограничиваем длину списка, чтобы он не рос бесконечно (только последние 10 нажатий)
                    user_input = user_input[-10:]

                    # Проверяем, совпадает ли последовательность с кодом Конами
                    if user_input == konami_code:
                        disco_mode = not disco_mode
                        user_input = []  # Очищаем после активации
                if event.key == pygame.K_ESCAPE:
                    if confirm_exit:
                        confirm_exit = False
                        exit_requested = False
                    else:
                        confirm_exit = True
                        confirm_selected = 0
                        exit_requested = True
                elif not confirm_exit:
                    if event.key == pygame.K_UP or event.key == pygame.K_w:
                        selected = (selected - 1) % len(menu_items)
                        keyboard_nav = True
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        selected = (selected + 1) % len(menu_items)
                        keyboard_nav = True
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        if selected == 0:
                            game_loop('endless')
                        elif selected == 1:
                            game_loop('timed')
                        elif selected == 2:
                            show_statistics()
                        elif selected == 3:
                            settings_menu()
                        elif selected == 4:
                            show_creators()
                        elif selected == 5:
                            confirm_exit = True
                            confirm_selected = 0
                            exit_requested = False
                else:
                    if event.key == pygame.K_UP or event.key == pygame.K_w:
                        confirm_selected = (confirm_selected - 1) % 2
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        confirm_selected = (confirm_selected + 1) % 2
                    elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        confirm_selected = 0
                    elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        confirm_selected = 1
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        if confirm_selected == 0:
                            pygame.quit()
                            sys.exit()
                        else:
                            confirm_exit = False
                            exit_requested = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if confirm_exit and dialog_yes_btn and dialog_no_btn:
                        if dialog_yes_btn.collidepoint(mouse_x, mouse_y):
                            pygame.quit()
                            sys.exit()
                        elif dialog_no_btn.collidepoint(mouse_x, mouse_y):
                            confirm_exit = False
                            exit_requested = False
                    else:
                        for i in range(len(menu_items)):
                            item_y = menu_start_y + i * menu_step
                            if (mouse_x > current_w // 2 - 150 and mouse_x < current_w // 2 + 150 and
                                    mouse_y > item_y - 20 and mouse_y < item_y + 20):
                                if i == 0:
                                    game_loop('endless')
                                elif i == 1:
                                    game_loop('timed')
                                elif i == 2:
                                    show_statistics()
                                elif i == 3:
                                    settings_menu()
                                elif i == 4:
                                    show_creators()
                                elif i == 5:
                                    confirm_exit = True
                                    confirm_selected = 0
                                    exit_requested = False
                                break

        if not confirm_exit:
            if mouse_moved or (current_time - last_mouse_move < mouse_cooldown):
                for i in range(len(menu_items)):
                    item_y = menu_start_y + i * menu_step
                    if (mouse_x > current_w // 2 - 150 and mouse_x < current_w // 2 + 150 and
                            mouse_y > item_y - 20 and mouse_y < item_y + 20):
                        if not keyboard_nav or (current_time - last_mouse_move < mouse_cooldown):
                            selected = i
                            keyboard_nav = False
            else:
                keyboard_nav = True

        angle += 0.5
        preview_cam.yaw = angle

        screen.fill(DARK_BLUE)

        for i in range(5):
            angle_offset = (angle + i * 72) % 360
            x = math.cos(math.radians(angle_offset)) * 5
            z = 5 + math.sin(math.radians(angle_offset)) * 3
            y = 1.5
            temp_target = Target(x, y, z)
            temp_target.draw(screen, preview_cam, current_w, current_h)

        draw_floor(screen, preview_cam, current_w, current_h)
        draw_roof(screen, preview_cam, current_w, current_h)

        menu_surface = pygame.Surface((menu_surface_width, menu_surface_height))
        menu_surface.set_alpha(200)
        menu_surface.fill(BLACK)
        screen.blit(menu_surface, (menu_surface_x, menu_surface_y))

        # --- ОТРИСОВКА ЗАГОЛОВКА С УЧЕТОМ ПАСХАЛКИ ---
        title_color = YELLOW
        if disco_mode:
            # Генерируем "диско-цвет" на основе текущего времени
            title_color = (
                int(127 + 127 * math.sin(current_time * 0.005)),
                int(127 + 127 * math.sin(current_time * 0.005 + 2)),
                int(127 + 127 * math.sin(current_time * 0.005 + 4))
            )

        title = font_title.render("Accurate", True, title_color)
        title_rect = title.get_rect(center=(current_w // 2, title_y))
        screen.blit(title, title_rect)

        # Используем увеличенный шрифт для Aim Trainer
        subtitle = font_subtitle.render("Aim Trainer", True, GRAY)
        subtitle_rect = subtitle.get_rect(center=(current_w // 2, subtitle_y))
        screen.blit(subtitle, subtitle_rect)

        y_pos = menu_start_y
        for i, item in enumerate(menu_items):
            color = YELLOW if i == selected else WHITE
            text = font_menu.render(item, True, color)
            text_rect = text.get_rect(center=(current_w // 2, y_pos))
            screen.blit(text, text_rect)
            y_pos += menu_step

        controls = font_info.render("W/S or UP/DOWN: Navigate | Mouse: Hover & Click | ENTER: Select | ESC: Exit", True,
                                    GRAY)
        controls_rect = controls.get_rect(center=(current_w // 2, controls_y))
        screen.blit(controls, controls_rect)

        # Диалог подтверждения выхода
        if confirm_exit:
            overlay = pygame.Surface((current_w, current_h))
            overlay.set_alpha(180)
            overlay.fill(BLACK)
            screen.blit(overlay, (0, 0))

            dialog_width = 420
            dialog_height = 160
            dialog_x = (current_w - dialog_width) // 2
            dialog_y = (current_h - dialog_height) // 2

            dialog_surface = pygame.Surface((dialog_width, dialog_height))
            dialog_surface.set_alpha(230)
            dialog_surface.fill(DARK_BLUE)
            screen.blit(dialog_surface, (dialog_x, dialog_y))
            pygame.draw.rect(screen, YELLOW, (dialog_x, dialog_y, dialog_width, dialog_height), 2)

            question_text = font_confirm.render("Exit the game?", True, WHITE)
            question_rect = question_text.get_rect(center=(current_w // 2, dialog_y + 45))
            screen.blit(question_text, question_rect)

            yes_color = GREEN if confirm_selected == 0 else GRAY
            no_color = RED if confirm_selected == 1 else GRAY

            yes_btn = pygame.Rect(dialog_x + 50, dialog_y + 90, 130, 40)
            no_btn = pygame.Rect(dialog_x + dialog_width - 180, dialog_y + 90, 130, 40)

            pygame.draw.rect(screen, yes_color, yes_btn, 2)
            pygame.draw.rect(screen, no_color, no_btn, 2)

            if yes_btn.collidepoint(mouse_x, mouse_y):
                pygame.draw.rect(screen, (50, 100, 50), yes_btn, 0)
                pygame.draw.rect(screen, GREEN, yes_btn, 2)
            if no_btn.collidepoint(mouse_x, mouse_y):
                pygame.draw.rect(screen, (100, 50, 50), no_btn, 0)
                pygame.draw.rect(screen, RED, no_btn, 2)

            yes_text = font_confirm.render("YES", True, yes_color)
            no_text = font_confirm.render("NO", True, no_color)

            yes_rect = yes_text.get_rect(center=yes_btn.center)
            no_rect = no_text.get_rect(center=no_btn.center)

            screen.blit(yes_text, yes_rect)
            screen.blit(no_text, no_rect)

        pygame.display.flip()
        clock.tick(60)

# Меню настроек
def settings_menu():
    global settings, screen

    pygame.mouse.set_visible(True)
    pygame.event.set_grab(False)

    current_w, current_h = screen.get_size()

    if current_w >= 1920:
        font_size = 36
        small_font_size = 28
        value_font_size = 32
    elif current_w >= 1280:
        font_size = 32
        small_font_size = 24
        value_font_size = 28
    else:
        font_size = 28
        small_font_size = 20
        value_font_size = 24

    font = pygame.font.Font(None, font_size)
    small_font = pygame.font.Font(None, small_font_size)
    value_font = pygame.font.Font(None, value_font_size)

    DISPLAY_MODES = {
        "Windowed (Stretched)": "stretched",
        "Windowed (Native)": "native",
        "Fullscreen": "fullscreen"
    }
    display_modes_list = list(DISPLAY_MODES.keys())

    if "display_mode" not in settings:
        if settings["fullscreen"]:
            settings["display_mode"] = "Fullscreen"
        else:
            settings["display_mode"] = "Windowed (Native)"

    resolution_names = list(RESOLUTIONS.keys())
    if settings["resolution"] not in resolution_names:
        settings["resolution"] = "1920x1080 (16:9 Full HD)"

    menu_items = [
        {"name": "Mouse Sensitivity", "value": settings["mouse_sensitivity"], "type": "slider", "min": 0.01, "max": 1.0,
         "step": 0.01},
        {"name": "Crosshair Size", "value": settings.get("crosshair_size", 1.0), "type": "slider", "min": 0.5,
         "max": 1.5, "step": 0.05},
        {"name": "Display Mode", "value": settings.get("display_mode", "Windowed (Native)"), "type": "display_mode",
         "options": display_modes_list},
        {"name": "Resolution", "value": settings["resolution"], "type": "resolution", "options": resolution_names},
        {"name": "FPS Limit", "value": settings.get("fps_limit", 0), "type": "fps_slider", "min": 0, "max": 1000,
         "step": 10},
        {"name": "Volume", "value": settings["volume"], "type": "slider", "min": 0.0, "max": 1.0, "step": 0.05},
        {"name": "Crosshair Color", "value": settings["crosshair_color"], "type": "color",
         "options": list(CROSSHAIR_COLORS.keys())},
        {"name": "Show Grid", "value": settings.get("show_grid", True), "type": "toggle", "options": ["Off", "On"]},
        {"name": "SAVE & RETURN", "type": "button"},
        {"name": "BACK", "type": "button"}
    ]

    selected = 0
    editing_slider = False

    keyboard_nav = True
    last_mouse_move = pygame.time.get_ticks()
    mouse_cooldown = 500

    running = True
    while running:
        current_w, current_h = screen.get_size()

        title_y = int(current_h * 0.08)
        start_y = int(current_h * 0.16)
        line_height = int(current_h * 0.055)
        bar_height = int(current_h * 0.015)
        hint_y = int(current_h * 0.85)
        controls_y = int(current_h * 0.92)

        name_x = int(current_w * 0.25)
        value_x = int(current_w * 0.65)
        bar_x = int(current_w * 0.55)
        bar_width = int(current_w * 0.2)
        arrows_x = int(current_w * 0.82)
        button_x = int(current_w * 0.55)
        button_width = int(current_w * 0.2)

        mouse_x, mouse_y = pygame.mouse.get_pos()
        current_time = pygame.time.get_ticks()

        mouse_moved = False
        for event in pygame.event.get(pygame.MOUSEMOTION):
            mouse_moved = True
            last_mouse_move = current_time

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if editing_slider:
                        editing_slider = False
                    else:
                        running = False
                elif not editing_slider:
                    if event.key == pygame.K_w:
                        selected = (selected - 1) % len(menu_items)
                        keyboard_nav = True
                    elif event.key == pygame.K_s:
                        selected = (selected + 1) % len(menu_items)
                        keyboard_nav = True
                    elif event.key == pygame.K_a or event.key == pygame.K_d:
                        item = menu_items[selected]
                        direction = 1 if event.key == pygame.K_d else -1

                        if item["type"] == "slider":
                            new_value = item["value"] + item["step"] * direction
                            item["value"] = max(item["min"], min(item["max"], new_value))
                            if item["name"] == "Mouse Sensitivity":
                                settings["mouse_sensitivity"] = item["value"]
                            elif item["name"] == "Crosshair Size":
                                settings["crosshair_size"] = item["value"]
                            elif item["name"] == "Volume":
                                settings["volume"] = item["value"]
                                if shot_sound:
                                    shot_sound.set_volume(settings["volume"])
                                    hit_sound.set_volume(settings["volume"])

                        elif item["type"] == "display_mode":
                            modes = item["options"]
                            current_idx = modes.index(item["value"])
                            new_idx = (current_idx + direction) % len(modes)
                            item["value"] = modes[new_idx]
                            settings["display_mode"] = item["value"]

                        elif item["type"] == "resolution":
                            res_names = item["options"]
                            current_idx = res_names.index(item["value"])
                            new_idx = (current_idx + direction) % len(res_names)
                            item["value"] = res_names[new_idx]
                            settings["resolution"] = item["value"]
                            w, h = RESOLUTIONS[item["value"]]
                            settings["screen_width"] = w
                            settings["screen_height"] = h

                        elif item["type"] == "color":
                            colors = item["options"]
                            current_idx = colors.index(item["value"])
                            new_idx = (current_idx + direction) % len(colors)
                            item["value"] = colors[new_idx]
                            settings["crosshair_color"] = item["value"]

                        elif item["type"] == "toggle":
                            if item["name"] == "Show Grid":
                                settings["show_grid"] = not settings["show_grid"]
                                item["value"] = settings["show_grid"]
                            else:
                                settings["fullscreen"] = not settings["fullscreen"]
                                item["value"] = settings["fullscreen"]

                        elif item["type"] == "fps_slider":
                            new_value = item["value"] + item["step"] * direction
                            item["value"] = max(item["min"], min(item["max"], new_value))
                            settings["fps_limit"] = item["value"]

                    elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        item = menu_items[selected]
                        if item["type"] == "button":
                            if item["name"] == "SAVE & RETURN":
                                save_settings(settings)
                                w, h = settings["screen_width"], settings["screen_height"]
                                display_mode = settings.get("display_mode", "Windowed (Native)")
                                if display_mode == "Fullscreen":
                                    screen = pygame.display.set_mode((w, h), pygame.FULLSCREEN | pygame.DOUBLEBUF)
                                elif display_mode == "Windowed (Native)":
                                    os.environ['SDL_VIDEO_CENTERED'] = '1'
                                    screen = pygame.display.set_mode((w, h), pygame.DOUBLEBUF)
                                else:
                                    os.environ['SDL_VIDEO_CENTERED'] = '1'
                                    screen = pygame.display.set_mode((w, h), pygame.RESIZABLE | pygame.DOUBLEBUF)
                                running = False
                            elif item["name"] == "BACK":
                                running = False
                        elif item["type"] in ["slider", "fps_slider"]:
                            editing_slider = True

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and not editing_slider:
                    item = menu_items[selected]
                    if item["type"] == "button":
                        if item["name"] == "SAVE & RETURN":
                            save_settings(settings)
                            w, h = settings["screen_width"], settings["screen_height"]
                            display_mode = settings.get("display_mode", "Windowed (Native)")
                            if display_mode == "Fullscreen":
                                screen = pygame.display.set_mode((w, h), pygame.FULLSCREEN | pygame.DOUBLEBUF)
                            elif display_mode == "Windowed (Native)":
                                os.environ['SDL_VIDEO_CENTERED'] = '1'
                                screen = pygame.display.set_mode((w, h), pygame.DOUBLEBUF)
                            else:
                                os.environ['SDL_VIDEO_CENTERED'] = '1'
                                screen = pygame.display.set_mode((w, h), pygame.RESIZABLE | pygame.DOUBLEBUF)
                            running = False
                        elif item["name"] == "BACK":
                            running = False
                    elif item["type"] in ["slider", "fps_slider"]:
                        editing_slider = True
                        bar_y = start_y + selected * line_height + int(line_height * 0.25)
                        if mouse_x >= bar_x and mouse_x <= bar_x + bar_width:
                            rel_x = mouse_x - bar_x
                            if rel_x < 0:
                                rel_x = 0
                            if rel_x > bar_width:
                                rel_x = bar_width
                            new_value = item["min"] + (rel_x / bar_width) * (item["max"] - item["min"])
                            steps = round((new_value - item["min"]) / item["step"])
                            new_value = item["min"] + steps * item["step"]
                            new_value = max(item["min"], min(item["max"], new_value))
                            item["value"] = new_value
                            if item["name"] == "Mouse Sensitivity":
                                settings["mouse_sensitivity"] = item["value"]
                            elif item["name"] == "Crosshair Size":
                                settings["crosshair_size"] = item["value"]
                            elif item["name"] == "Volume":
                                settings["volume"] = item["value"]
                                if shot_sound:
                                    shot_sound.set_volume(settings["volume"])
                                    hit_sound.set_volume(settings["volume"])
                            elif item["name"] == "FPS Limit":
                                settings["fps_limit"] = item["value"]
                    elif item["type"] in ["display_mode", "resolution", "color", "toggle"]:
                        if item["type"] == "display_mode":
                            modes = item["options"]
                            current_idx = modes.index(item["value"])
                            new_idx = (current_idx + 1) % len(modes)
                            item["value"] = modes[new_idx]
                            settings["display_mode"] = item["value"]
                        elif item["type"] == "resolution":
                            res_names = item["options"]
                            current_idx = res_names.index(item["value"])
                            new_idx = (current_idx + 1) % len(res_names)
                            item["value"] = res_names[new_idx]
                            settings["resolution"] = item["value"]
                            w, h = RESOLUTIONS[item["value"]]
                            settings["screen_width"] = w
                            settings["screen_height"] = h
                        elif item["type"] == "color":
                            colors = item["options"]
                            current_idx = colors.index(item["value"])
                            new_idx = (current_idx + 1) % len(colors)
                            item["value"] = colors[new_idx]
                            settings["crosshair_color"] = item["value"]
                        elif item["type"] == "toggle":
                            if item["name"] == "Show Grid":
                                settings["show_grid"] = not settings["show_grid"]
                                item["value"] = settings["show_grid"]
                            else:
                                settings["fullscreen"] = not settings["fullscreen"]
                                item["value"] = settings["fullscreen"]

            elif event.type == pygame.MOUSEMOTION:
                if editing_slider and event.buttons[0]:
                    item = menu_items[selected]
                    if item["type"] in ["slider", "fps_slider"]:
                        rel_x = mouse_x - bar_x
                        if rel_x < 0:
                            rel_x = 0
                        if rel_x > bar_width:
                            rel_x = bar_width
                        new_value = item["min"] + (rel_x / bar_width) * (item["max"] - item["min"])
                        steps = round((new_value - item["min"]) / item["step"])
                        new_value = item["min"] + steps * item["step"]
                        new_value = max(item["min"], min(item["max"], new_value))
                        item["value"] = new_value
                        if item["name"] == "Mouse Sensitivity":
                            settings["mouse_sensitivity"] = item["value"]
                        elif item["name"] == "Crosshair Size":
                            settings["crosshair_size"] = item["value"]
                        elif item["name"] == "Volume":
                            settings["volume"] = item["value"]
                            if shot_sound:
                                shot_sound.set_volume(settings["volume"])
                                hit_sound.set_volume(settings["volume"])
                        elif item["name"] == "FPS Limit":
                            settings["fps_limit"] = item["value"]

            elif event.type == pygame.MOUSEBUTTONUP:
                if editing_slider:
                    editing_slider = False

        if not editing_slider:
            if mouse_moved or (current_time - last_mouse_move < mouse_cooldown):
                y_offset_check = start_y
                for i in range(len(menu_items)):
                    item_rect = pygame.Rect(name_x - 20, y_offset_check - 15, current_w - name_x - 100, line_height)
                    if item_rect.collidepoint(mouse_x, mouse_y):
                        if not keyboard_nav or (current_time - last_mouse_move < mouse_cooldown):
                            selected = i
                            keyboard_nav = False
                    y_offset_check += line_height
            else:
                keyboard_nav = True

        screen.fill(DARK_BLUE)

        title = font.render("SETTINGS", True, YELLOW)
        title_rect = title.get_rect(center=(current_w // 2, title_y))
        screen.blit(title, title_rect)

        y_offset = start_y
        for i, item in enumerate(menu_items):
            color = YELLOW if i == selected else WHITE

            name_text = font.render(item["name"], True, color)
            name_rect = name_text.get_rect(x=name_x, y=y_offset)
            screen.blit(name_text, name_rect)

            if item["type"] == "slider":
                value_text = value_font.render(f"{item['value']:.2f}", True, LIGHT_GRAY)
                value_rect = value_text.get_rect(x=value_x, y=y_offset - 15)
                screen.blit(value_text, value_rect)

                bar_y = y_offset + int(line_height * 0.2)
                pygame.draw.rect(screen, GRAY, (bar_x, bar_y, bar_width, bar_height))
                fill_width = int(bar_width * ((item["value"] - item["min"]) / (item["max"] - item["min"])))
                pygame.draw.rect(screen, GREEN, (bar_x, bar_y, fill_width, bar_height))

                marker_x = bar_x + fill_width
                pygame.draw.rect(screen, WHITE, (marker_x - 4, bar_y - 4, 8, bar_height + 8))

                if i == selected and not editing_slider:
                    arrows = small_font.render("A  D or Drag", True, GREEN)
                    arrows_rect = arrows.get_rect(x=arrows_x, y=y_offset)
                    screen.blit(arrows, arrows_rect)
                elif i == selected and editing_slider:
                    arrows = small_font.render("Drag mouse", True, YELLOW)
                    arrows_rect = arrows.get_rect(x=arrows_x, y=y_offset)
                    screen.blit(arrows, arrows_rect)

            elif item["type"] == "fps_slider":
                if item["value"] == 0:
                    value_text = value_font.render("Unlimited", True, LIGHT_GRAY)
                else:
                    value_text = value_font.render(f"{item['value']:.0f}", True, LIGHT_GRAY)
                value_rect = value_text.get_rect(x=value_x, y=y_offset - 15)
                screen.blit(value_text, value_rect)

                bar_y = y_offset + int(line_height * 0.2)
                pygame.draw.rect(screen, GRAY, (bar_x, bar_y, bar_width, bar_height))
                fill_width = int(bar_width * ((item["value"] - item["min"]) / (item["max"] - item["min"])))
                pygame.draw.rect(screen, GREEN, (bar_x, bar_y, fill_width, bar_height))

                marker_x = bar_x + fill_width
                pygame.draw.rect(screen, WHITE, (marker_x - 4, bar_y - 4, 8, bar_height + 8))

                if i == selected and not editing_slider:
                    arrows = small_font.render("A  D or Drag", True, GREEN)
                    arrows_rect = arrows.get_rect(x=arrows_x, y=y_offset)
                    screen.blit(arrows, arrows_rect)
                elif i == selected and editing_slider:
                    arrows = small_font.render("Drag mouse", True, YELLOW)
                    arrows_rect = arrows.get_rect(x=arrows_x, y=y_offset)
                    screen.blit(arrows, arrows_rect)

            elif item["type"] in ["display_mode", "resolution", "color", "toggle"]:
                if item["type"] == "toggle":
                    value_text = value_font.render("On" if item["value"] else "Off", True, LIGHT_GRAY)
                else:
                    value_text = small_font.render(item["value"], True, LIGHT_GRAY)
                value_rect = value_text.get_rect(x=value_x, y=y_offset)
                screen.blit(value_text, value_rect)

                if i == selected:
                    arrows = small_font.render("A  D or Click", True, GREEN)
                    arrows_rect = arrows.get_rect(x=arrows_x + 50, y=y_offset)
                    screen.blit(arrows, arrows_rect)

            elif item["type"] == "button":
                button_rect = pygame.Rect(button_x, y_offset - 10, button_width, 40)
                if button_rect.collidepoint(mouse_x, mouse_y) and not editing_slider:
                    pygame.draw.rect(screen, (100, 150, 100), button_rect, 2)
                else:
                    pygame.draw.rect(screen, GREEN if i == selected else GRAY, button_rect, 2)
                value_text = font.render(item["name"], True, color)
                value_rect = value_text.get_rect(center=(button_rect.centerx, button_rect.centery))
                screen.blit(value_text, value_rect)

            y_offset += line_height

        if editing_slider:
            hint = small_font.render("Drag mouse to adjust value | Release to finish", True, YELLOW)
        else:
            current_item = menu_items[selected]
            if current_item["type"] == "button":
                hint = small_font.render("Click or press ENTER to confirm", True, GREEN)
            elif current_item["type"] in ["slider", "fps_slider"]:
                hint = small_font.render("Press A/D, drag with mouse, or click to change values", True, GREEN)
            else:
                hint = small_font.render("Press A/D or click to change values", True, GREEN)

        hint_rect = hint.get_rect(center=(current_w // 2, hint_y))
        screen.blit(hint, hint_rect)

        controls = small_font.render("W/S: Navigate | Mouse: Hover & Click | A/D: Change | ESC: Back", True, GRAY)
        controls_rect = controls.get_rect(center=(current_w // 2, controls_y))
        screen.blit(controls, controls_rect)

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main_menu()
