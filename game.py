import pygame
import random
import string
import threading  
from gtts import gTTS
import os
import tempfile
import sys
import speech_recognition as sr
import vosk
import sounddevice as sd
import queue
import json
import time
pygame.init()
clock = pygame.time.Clock()

# Title và icon
pygame.display.set_caption("English Game")
icon = pygame.image.load(r'assets/char/dinosaur.png')

# Background và các hình ảnh khác
screen = pygame.display.set_mode((800, 600))
bg = pygame.image.load(r'assets/background/bg4.png')
tree = pygame.image.load(r'assets/object/tree7.png')
dino = pygame.image.load(r'assets/char/chicken4.png')
dino = pygame.transform.scale(dino, (90, 80))  # Resize nhân vật
tree = pygame.transform.scale(tree, (90, 80))  # Resize cây

baloo_font = pygame.font.Font('assets/font/Baloo2-Bold.ttf', 24)

# Load âm thanh
sound1 = pygame.mixer.Sound(r'sound/tick.wav')
sound2 = pygame.mixer.Sound(r'sound/te.wav')
pygame.mixer.music.load('sound/music2.mp3')
pygame.mixer.music.set_volume(0.3)  
pygame.mixer.music.play(-1)  # Lặp vô hạn


# Khởi tạo các biến game ban đầu
sound_on=True
score = 0
high_score = 0
bg_x, bg_y = 0, 0
tree_x, tree_y = 750, 460
dino_x, dino_y = 100, 460
x_def = 5
y_def = 12  # Tốc độ rơi của dino
jump = False
gameplay = False
main_menu = True
vocab_menu = False
game_over_flag = False  
paused = False
letters = []
letter_spawn_timer = random.randint(60, 120)






def voice_listener():
    global jump, gameplay, dino_y, game_over_flag
    voice_q = queue.Queue()
    model = vosk.Model("model")
    samplerate = 16000

    def callback(indata, frames, time, status):
        if status:
            print(status)
        voice_q.put(bytes(indata))

    with sd.RawInputStream(samplerate=samplerate, blocksize= 256, dtype='int16',
                           channels=1, callback=callback):
        rec = vosk.KaldiRecognizer(model, samplerate, '["jump"]')
        print("Say 'jump' to control the character:")

        while True:
            try:
                data = voice_q.get(timeout=0.05)
                # Xử lý partial trước
                partial = json.loads(rec.PartialResult())
                ptext = partial.get("partial", "")
                if "jump" in ptext and gameplay and not game_over_flag and not jump and dino_y >= 460:
                    jump = True
                    sound1.play()
                # Sau đó mới xử lý kết quả đầy đủ
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    text = result.get("text", "")
                    print(f"You said: {text}")
                    if "jump" in text and gameplay and not game_over_flag and not jump and dino_y >= 460:
                        jump = True
                        sound1.play()
            except Exception as e:
                print("Error in voice loop:", e)



def save_collected_words():
    with open("collected_words.txt", "w", encoding="utf-8") as file:
        for word in collected_words:
            file.write(word + "\n")

def load_collected_words():
    collected = set()
    if os.path.exists("collected_words.txt"):
        with open("collected_words.txt", "r", encoding="utf-8") as file:
            for line in file:
                collected.add(line.strip())
    return collected
collected_words = load_collected_words()



# Hàm reset vị trí các đối tượng khi khởi động lại trò chơi
def reset_game_positions():
    global bg_x, tree_x, dino_x, dino_y, jump, letter_spawn_timer
    bg_x = 0
    tree_x = 750
    dino_x = 100
    dino_y = 460
    jump = False
    letter_spawn_timer = random.randint(60, 120)

# Hàm đọc file từ vựng và chuyển đổi thành từ điển
def load_vocabulary(file_path):
    word_dict = {}
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip().replace('"', '').replace(',', '')
            word, meaning = line.split(': ')
            word_dict[word] = meaning
    return word_dict

# Hàm lưu high score vào file
def save_high_score(score):
    with open("high_score.txt", "w") as file:
        file.write(str(score))

# Hàm tải high score từ file
def load_high_score():
    if os.path.exists("high_score.txt"):
        with open("high_score.txt", "r") as file:
            return int(file.read().strip())
    return 0  # Nếu không có file, mặc định là 0

# Gán high_score khi khởi động game
high_score = load_high_score()


button_font = pygame.font.Font('assets/font/Baloo2-Bold.ttf', 28)

def draw_pixel_button(text, x, y, width, height, color=(0, 128, 255), hover_color=(0, 180, 255), text_color=(255, 255, 255)):
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()

    button_rect = pygame.Rect(x, y, width, height)

    # Hover effect
    if button_rect.collidepoint(mouse):
        pygame.draw.rect(screen, hover_color, button_rect, border_radius=8)
    else:
        pygame.draw.rect(screen, color, button_rect, border_radius=8)

    # Text render
    font = pygame.font.Font('assets/font/Baloo2-Bold.ttf', 28)
    text_surf = font.render(text, True, text_color)
    screen.blit(text_surf, (
        x + (width - text_surf.get_width()) // 2,
        y + (height - text_surf.get_height()) // 2
    ))

    return button_rect

def draw_outlined_text(text, font, x, y, main_color, outline_color):
    outline_offsets = [(-2, 0), (2, 0), (0, -2), (0, 2)]
    for ox, oy in outline_offsets:
        outline_surf = font.render(text, True, outline_color)
        screen.blit(outline_surf, (x + ox, y + oy))

    main_surf = font.render(text, True, main_color)
    screen.blit(main_surf, (x, y))




# Hiển thị màn hình chính
def show_main_menu():
    screen.blit(bg, (0, 0)) 

    # Vẽ nhân vật gà đứng ở góc dưới
    screen.blit(dino, (100, 460))  

    vertical_offset = 10 

    
    title_font = pygame.font.Font('assets/font/Baloo2-Bold.ttf', 48)
    draw_outlined_text(
        'English Game',
        title_font,
        (screen.get_width() - title_font.size('English Game')[0]) // 2,
        50 + vertical_offset,
        (255, 215, 0),   # Màu chính
        (0, 0, 0)        # Màu viền
    )


    center_x = (screen.get_width() - 200) // 2
    sound_button = draw_pixel_button(
    "Sound: ON" if sound_on else "Sound: OFF",
    center_x, 500 + vertical_offset, 200, 50,
    color=(180, 180, 180), hover_color=(180, 180, 255)
)



    # High Score
    high_font = pygame.font.Font('assets/font/Baloo2-Bold.ttf', 28)
    hs_text = high_font.render(f'High Score: {high_score}', True, (255, 0, 0))
    hs_rect = hs_text.get_rect(center=(screen.get_width() // 2, 180))
    border_rect = pygame.Rect(hs_rect.x - 10, hs_rect.y - 5, hs_rect.width + 20, hs_rect.height + 10)
    pygame.draw.rect(screen, (255, 230, 230), border_rect, border_radius=12)
    pygame.draw.rect(screen, (255, 0, 0), border_rect, 2, border_radius=12)
    screen.blit(hs_text, hs_rect)

    # Các nút
    center_x = (screen.get_width() - 200) // 2
    play_button = draw_pixel_button("Play", center_x, 220 + vertical_offset, 200, 50, color=(0, 128, 255), hover_color=(0, 180, 255))
    vocab_button = draw_pixel_button("Vocabulary", center_x, 290 + vertical_offset, 200, 50, color=(0, 0, 200), hover_color=(0, 0, 255))
    review_button = draw_pixel_button("Review", center_x, 360 + vertical_offset, 200, 50, color=(255, 204, 0), hover_color=(255, 229, 80), text_color=(0, 0, 0))
    reset_button = draw_pixel_button("Reset", center_x, 430 + vertical_offset, 200, 50, color=(255, 80, 80), hover_color=(255, 0, 0))

    return play_button, vocab_button, review_button, reset_button, sound_button



def review_menu():
    global running
    review_font = pygame.font.Font('assets/font/Baloo2-Bold.ttf', 24)
    review_running = True

    word_list = list(word_dict.items())
    scroll_offset = 0
    max_display = 10
    item_height = 40
    scroll_speed = 1

    while review_running:
       
         # Dùng background chính
        screen.blit(bg, (0, 0))
        # Phủ lớp trắng mờ để dễ đọc chữ
        overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
        overlay.fill((255, 255, 255, 180))
        screen.blit(overlay, (0, 0))


        draw_outlined_text(
            "Vocabulary Review",
            review_font,
            (screen.get_width() - review_font.size("Vocabulary Review")[0]) // 2,
            30,
            (0, 0, 0),      
            (255, 255, 255) 
)

        # Hiển thị các từ dựa trên scroll offset
        start_index = scroll_offset
        end_index = min(start_index + max_display, len(word_list))
        for i, (word, meaning) in enumerate(word_list[start_index:end_index]):
            color = (0, 200, 0) if word in collected_words else (50, 50, 50)
            word_surface = review_font.render(f"{word} - {meaning}", True, color)
            screen.blit(word_surface, (80, 80 + i * item_height))

        # Nút Back
        back_button = draw_pixel_button("Back", 325, 520, 150, 50, color=(200, 200, 200), hover_color=(220, 220, 220), text_color=(0, 0, 0))

        # Vẽ thanh cuộn (scrollbar)
        total_items = len(word_list)
        if total_items > max_display:
            bar_height = 400
            scrollbar_height = max(40, int(bar_height * max_display / total_items))
            scrollbar_pos = int((scroll_offset / (total_items - max_display)) * (bar_height - scrollbar_height))

            pygame.draw.rect(screen, (230, 230, 230), (750, 80, 10, bar_height))  # Nền thanh cuộn
            pygame.draw.rect(screen, (120, 120, 120), (750, 80 + scrollbar_pos, 10, scrollbar_height))  # Thanh cuộn

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.collidepoint(pygame.mouse.get_pos()):
                    review_running = False
                # Cuộn bằng bánh xe chuột
                if event.button == 4:  # Scroll up
                    if scroll_offset > 0:
                        scroll_offset -= scroll_speed
                elif event.button == 5:  # Scroll down
                    if scroll_offset + max_display < total_items:
                        scroll_offset += scroll_speed

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DOWN and scroll_offset + max_display < total_items:
                    scroll_offset += scroll_speed
                elif event.key == pygame.K_UP and scroll_offset > 0:
                    scroll_offset -= scroll_speed



def pause_menu():
    global running, paused, main_menu, gameplay, game_over_flag, score,sound_on
    big_font = pygame.font.Font('assets/font/Arial_Bold.ttf', 60)

    while paused:
      
        screen.blit(bg, (0, 0))
        # Phủ lớp trắng mờ toàn màn hình
        overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
        overlay.fill((255, 255, 255, 180))  # Trắng mờ, alpha 180
        screen.blit(overlay, (0, 0))
     

        # Tiêu đề "PAUSED"
        pause_text = big_font.render('PAUSED', True, (255, 255, 255))
        screen.blit(pause_text, ((800 - pause_text.get_width()) // 2, 130))

        draw_outlined_text(
            'PAUSED',
             big_font,
            (800 - big_font.size('PAUSED')[0]) // 2,
            130,
            (0, 0, 0),   
            (255, 255, 255)        
)


        # Vẽ các nút
        resume_button = draw_pixel_button("RESUME", 300, 220, 200, 50, color=(255, 165, 0), hover_color=(255, 200, 0))
        menu_button   = draw_pixel_button("MENU",   300, 290, 200, 50, color=(0, 180, 255), hover_color=(0, 220, 255))
        quit_button   = draw_pixel_button("QUIT",   300, 360, 200, 50, color=(255, 80, 80), hover_color=(255, 0, 0))
        sound_button  = draw_pixel_button(
            "Sound: ON" if sound_on else "Sound: OFF",
            300, 430, 200, 50,
            color=(180, 180, 180), hover_color=(120, 120, 120)
        )
        pygame.display.update()

        # Xử lý sự kiện
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_SPACE):
                    paused = False
                    return

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if resume_button.collidepoint(mouse_pos):
                    paused = False
                    return
                elif menu_button.collidepoint(mouse_pos):
                    paused = False
                    gameplay = False
                    game_over_flag = False
                    main_menu = True
                    score = 0  # reset điểm nếu cần
                    return
                elif quit_button.collidepoint(mouse_pos):
                    pygame.quit()
                    sys.exit()
                elif sound_button.collidepoint(mouse_pos):
                    sound_on = not sound_on
                    if sound_on:
                        pygame.mixer.music.set_volume(0.3)
                    else:
                        pygame.mixer.music.set_volume(0.0)



# Hiển thị màn hình chọn chủ đề từ vựng
def show_vocab_menu():
    screen.blit(bg, (0, 0))
    screen.blit(dino, (100, 460))

    title_text = game_font.render('Choose Vocabulary', True, (0, 0, 0))
    screen.blit(title_text, (screen.get_width() // 2 - title_text.get_width() // 2, 30))

    categories = [
        ("Fruits", (255, 204, 102)),
        ("Animals", (144, 238, 144)),
        ("Home", (173, 216, 230)),
        ("Job", (255, 182, 193)),
        ("Body Parts", (255, 255, 153)),
        ("School", (204, 153, 255)),
        ("Color", (255, 255, 255)),
        ("Shapes", (192, 192, 192)),
        ("Food", (255, 218, 185)),
        ("Weather", (135, 206, 250)),
    ]

    buttons = []
    cols = 2
    rows = len(categories) // cols
    button_width = 200
    button_height = 50
    spacing_x = 40
    spacing_y = 20
    start_x = (screen.get_width() - (button_width * cols + spacing_x)) // 2
    start_y = 100

    for index, (text, color) in enumerate(categories):
        row = index % rows
        col = index // rows
        x = start_x + col * (button_width + spacing_x)
        y = start_y + row * (button_height + spacing_y)

        btn_rect = draw_pixel_button(
            text=text,
            x=x,
            y=y,
            width=button_width,
            height=button_height,
            color=color,
            hover_color=(min(color[0]+20, 255), min(color[1]+20, 255), min(color[2]+20, 255)),
            text_color=(0, 0, 0)
        )
        buttons.append((text, btn_rect))

    return buttons





# Các biến từ vựng và trạng thái từ cần thu thập
word_dict = {}
words = []
current_word = ""
expected_index = 0
collected_letters = []

# Hàm kiểm tra va chạm giữa dino và cây (tree) dựa trên tọa độ hiện tại
def checkvc():
    dino_rect = pygame.Rect(dino_x + 15, dino_y + 20, dino.get_width() - 30, dino.get_height() - 15)
    tree_rect = pygame.Rect(tree_x + 20, tree_y + 5, tree.get_width() - 40, tree.get_height() - 20)  

    if dino_rect.colliderect(tree_rect):
        sound2.play()
        return False
    return True


# Khởi tạo font hiển thị
game_font = pygame.font.Font('assets/font/Arial_Bold.ttf', 20)
word_font = pygame.font.Font('assets/font/Baloo2-Bold.ttf', 26)

def show_score(): 
    draw_outlined_text(f'High Score: {int(high_score)}', word_font, screen.get_width() - 200, 50, (255, 0, 0), (255, 255, 255))
    draw_outlined_text(f'Score: {int(score)}', word_font, screen.get_width() - 200, 20, (255, 0, 0), (255, 255, 255))

    if not gameplay:
        # Tăng kích thước font Game Over
        big_font = pygame.font.Font('assets/font/Baloo2-Bold.ttf', 70)
       
        draw_outlined_text(
            'GAME OVER',
            big_font,
            (screen.get_width() - big_font.size('GAME OVER')[0]) // 2,
            screen.get_height() // 3,
            (255, 0, 0),  # Màu chính
            (255, 255, 255)  # Màu viền
        )


        # Vẽ nút "Back"
        back_button = draw_pixel_button("Back", 325, 300, 150, 50, color=(0, 200, 0), hover_color=(0, 255, 0), text_color=(0, 0, 0))
        return back_button
    return None



def show_word():

    draw_outlined_text(f'TARGET: {current_word}', word_font, 30, 20, (0,0,255), (255, 255, 255))
    draw_outlined_text(f'MEANING: {word_dict[current_word]}', word_font, 30, 52, (30,144,255), (255,255,255))
    # draw_outlined_text("".join(collected_letters), word_font, 30, 85, (0,255,0), (0, 0, 0))
        # Hiển thị từ thu thập với khoảng trắng và dấu gạch dưới cho phần chưa thu thập
    display_word = ""
    collected_i = 0
    for c in current_word:
        if c == " ":
            display_word += " "
        elif collected_i < len(collected_letters):
            display_word += collected_letters[collected_i]
            collected_i += 1
        else:
            display_word += "_"

    draw_outlined_text(display_word, word_font, 30, 85, (0,255,0), (0, 0, 0))

 

# Hàm tạo chữ cái ngẫu nhiên, với 75% là chữ cần thu thập
def generate_letter():
    if len(letters) >= 2:
        return None
    # Nếu cây đang ở gần nhân vật, không sinh chữ cái để tránh va chạm
    if tree_x - dino_x < 150:
        return None
    # Bỏ qua các ký tự khoảng trắng khi sinh chữ
    global expected_index, current_word
    while expected_index < len(current_word) and current_word[expected_index] == " ":
        expected_index += 1

    if expected_index < len(current_word):
        if random.random() < 0.75:
            letter_char = current_word[expected_index]
        else:
            letter_char = random.choice([l for l in string.ascii_uppercase if l != current_word[expected_index]])

        min_safe_distance = 350  # Tăng khoảng cách giữa cây và chữ
        letter_x = max(550, tree_x + min_safe_distance)  # Đẩy chữ ra xa cây

        letter_y = 300  # Đặt chữ ở giữa màn hình để dễ thu thập

        # Tránh chữ xuất hiện chồng lên nhau
        if letters:
            last_letter = letters[-1]
            while abs(letter_x - last_letter["x"]) < 200:
                letter_x += random.randint(30, 60)

        return {
            "letter": letter_char,
            "x": letter_x,
            "y": letter_y,  
            "speed": x_def,
            
        }
    return None





# Hàm đọc từ bằng gTTS
def read_word(word):
    tts = gTTS(text=word, lang='en')
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
    temp_file.close()
    tts.save(temp_file.name)
    sound = pygame.mixer.Sound(temp_file.name)
    sound.play()


     # Chờ âm thanh phát xong
    while sound.get_num_channels() > 0:
        pygame.time.Clock().tick(10)
    os.remove(temp_file.name)
# ---------------------------
# Vòng lặp chính của game
# ---------------------------
running = True
threading.Thread(target=voice_listener, daemon=True).start()
while running:
    clock.tick(60)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if gameplay and not game_over_flag and not main_menu:
                paused = True  # Kích hoạt trạng thái PAUSE
                pause_menu()  # Hiển thị menu PAUSE
        if paused:
            continue  # Nếu đang Pause, không cập nhật game
        # Nếu đang ở trạng thái Game Over, cho phép nhấn SPACE để khởi động lại
        if game_over_flag:
            back_button = show_score()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    game_over_flag = False
                    score = 0
                    gameplay = True
                    collected_letters = []
                    expected_index = 0
                    current_word = random.choice(words)
                    letters.clear()
                    reset_game_positions()  
            elif event.type == pygame.MOUSEBUTTONDOWN:
            # Nhấn chuột vào nút "Back" để quay về menu chính
                mouse_pos = pygame.mouse.get_pos()
                if back_button and back_button.collidepoint(mouse_pos):
                    game_over_flag = False
                    main_menu = True  # Quay về màn hình chính
                    gameplay = False
                    vocab_menu = False
                    score = 0
                    continue
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and gameplay:
                if dino_y == 460:
                    jump = True
                    sound1.play()
            if event.key == pygame.K_SPACE and not gameplay and not main_menu:
                gameplay = True
                score = 0
                collected_letters = []
                expected_index = 0
                current_word = random.choice(words)
                letters.clear()
                reset_game_positions()
                
        #vocabulary menu
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            if main_menu:
                play_button, vocab_button, review_button, reset_button,sound_button = show_main_menu()

                
                if play_button.collidepoint(mouse_pos):
                    score = 0
                    main_menu = False
                    gameplay = True
                    game_over_flag = False
                    word_dict = load_vocabulary('data/fruits.txt')
                    words = list(word_dict.keys())
                    current_word = random.choice(words)
                    expected_index = 0
                    collected_letters = []
                    letters.clear()
                    reset_game_positions()
                elif vocab_button.collidepoint(mouse_pos):
                    main_menu = False
                    vocab_menu = True
                elif review_button.collidepoint(mouse_pos):
                    # Mở màn hình review
                    review_menu()
                elif reset_button.collidepoint(mouse_pos):
                     # Xử lý nút Reset
                    high_score = 0
                    collected_words.clear()
                    save_high_score(high_score)
                    save_collected_words()
                    print("Game reset thành công!")
                elif sound_button.collidepoint(mouse_pos):
                    sound_on = not sound_on
                    if sound_on:
                        pygame.mixer.music.set_volume(0.3)
                    else:
                        pygame.mixer.music.set_volume(0.0)

            elif vocab_menu:
                category_buttons = show_vocab_menu()
                for name, btn in category_buttons:
                    if btn.collidepoint(mouse_pos):
                        vocab_menu = False
                        gameplay = True
                        game_over_flag = False
                        word_dict = load_vocabulary(f'data/{name.lower().replace(" ", "_")}.txt')
                        words = list(word_dict.keys())
                        current_word = random.choice(words)
                        expected_index = 0
                        collected_letters = []
                        letters.clear()
                        reset_game_positions()
            # ESC để quay lại
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                vocab_menu = False
                main_menu = True
                words = list(word_dict.keys())
                current_word = random.choice(words)
                expected_index = 0
                collected_letters = []
                letters.clear()
                reset_game_positions()
            
    if main_menu:
        play_button, vocab_button,review_button, reset_button, sound_button = show_main_menu()
    elif vocab_menu:
        fruit_button, animal_button, job_button,home_button,school_button,body_button,color_button,shape_button,weather_button,food_button = show_vocab_menu()
    elif gameplay:
        # Cập nhật nền
        bg_hcn = screen.blit(bg, (bg_x, bg_y))
        bg2_hcn = screen.blit(bg, (bg_x + 800, bg_y))
        bg_x -= x_def
        if bg_x == -800:
            bg_x = 0
        
        # Cập nhật cây
        tree_hcn = screen.blit(tree, (tree_x, tree_y))
        tree_x -= x_def
        if tree_x == -20:
            tree_x = 750
        
        # Hiển thị dino
        dino_hcn = screen.blit(dino, (dino_x, dino_y))
        if dino_y >= 150 and jump:
            dino_y -= y_def
        else:
            jump = False
        if dino_y < 460 and not jump:
            dino_y += y_def
        
        # Tạo chữ cái mới theo timer
        if letter_spawn_timer <= 0:
            new_letter = generate_letter()
            if new_letter is not None:
                letters.append(new_letter)
            letter_spawn_timer = random.randint(60, 120)
        else:
            letter_spawn_timer -= 1

        letter_font = pygame.font.Font('assets/font/Baloo2-Bold.ttf', 38)
        # Di chuyển chữ và kiểm tra va chạm với dino
        for letter in letters[:]:
            letter["x"] -= letter["speed"]
            
            draw_outlined_text(letter["letter"], letter_font, letter["x"], letter["y"], (238,130,238), (0, 0, 0))
            letter_rect = pygame.Rect(letter["x"], letter["y"], 38, 38)
            if letter["x"] < -50:
                letters.remove(letter)
                continue
            # Bỏ qua khoảng trắng trong target trước khi so sánh
            while expected_index < len(current_word) and current_word[expected_index] == " ":
                expected_index += 1

             # Nếu đã thu hết chữ, không cần so sánh nữa
            if expected_index >= len(current_word):
                continue
            
            if letter["letter"] != current_word[expected_index] and letter["x"] < dino_x - 50:
                letters.remove(letter)
                continue
            if dino_hcn.colliderect(letter_rect):
                if letter["letter"] == current_word[expected_index]:
                    # if expected_index < len(current_word) and letter["letter"] == current_word[expected_index]:
                    collected_letters.append(letter["letter"])
                    expected_index += 1
                    letters.remove(letter)
                else:
                    gameplay = False
                    game_over_flag = True
                    sound2.play()
                    break

            if len(letters) > 15:
                letters = letters[-15:]  



        if "".join(collected_letters) == current_word.replace(" ", ""):
            score += 10
            if score > high_score:
                high_score = score
                save_high_score(high_score)

            collected_words.add(current_word)  
            save_collected_words()     
            collected_letters = []
            expected_index = 0
            # read_word(current_word)
            threading.Thread(target=read_word, args=(current_word,), daemon=True).start()
            current_word = random.choice(words)
            letters.clear()
        
        # Kiểm tra va chạm với cây
        if not checkvc():
            gameplay = False
            game_over_flag = True
        
        show_score()
        show_word()
    elif game_over_flag:
        show_score()
    
    pygame.display.update()

pygame.quit()
