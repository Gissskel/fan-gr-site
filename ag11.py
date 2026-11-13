"""Fan Group — Elizaveta Maleina & Matvey Samokhin.

Оптимизированная версия ag6.py. Внешний вид и маршруты те же:
/, /about, /second, /photos
"""

import hashlib
import os
import re
from datetime import timedelta

from flask import Flask, Response, request

app = Flask(__name__)

# Статика (картинки, видео) кэшируется браузером на неделю
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = timedelta(days=7)

# Gzip-сжатие ответов, если установлен flask-compress (pip install flask-compress)
try:
    from flask_compress import Compress

    Compress(app)
except ImportError:
    pass


# ============================================================
# ДАННЫЕ
# ============================================================

PHOTO_BASE = "https://figure-skaters.ru/i/"
PHOTOS = [
    "35/5c/355c1ffc23-c.jpeg",
    "85/5f/855f8baf2e-c.jpeg",
    "28/c5/28c5b550cd.jpg",
    "c3/06/c30685bcec-c.jpeg",
    "74/4a/744a92566c-c.jpeg",
    "f8/9a/f89a21ea30-c.jpeg",
    "3f/7b/3f7bc0c00c-c.jpeg",
    "e0/34/e034c01399-c.jpeg",
    "82/15/8215a8c76a-c.jpeg",
    # Новые фотографии
    "f5/f5/f5f59a7415.jpg",
    "77/cf/77cfa6529d.jpg",
    "92/cc/92cc54f1e5.jpg",
    "3f/7b/3f7bc0c00c.jpg",
    "9f/b4/9fb498e401.jpg",
    "5c/81/5c818d7a2a.jpg",
    "78/40/784031d4c2.jpg",
    "3e/f2/3ef2905aa1.jpg",
    "d1/b2/d1b2dd1694.jpg",
    "fb/a0/fba0bb62f9.jpg",
    "7c/a2/7ca2bda1a8.jpg",
    "f2/98/f298f5e571.jpg",
    "d0/a3/d0a35df84b.jpg",
    "12/49/124909a4ba.jpg",
    "5d/c1/5dc17e6726.jpg"
]

# Главное видео (левая треть) и четыре видео в сетке 2×2 (правые 2/3).
# Файлы: /static/videos/<имя>.mp4 и <имя>.webm
MAIN_VIDEO = ("videoGlavnoe", "🌟 Трудимся ВСЕГДА !!!", ("mp4", "webm", "mov"))
GRID_VIDEOS = [(f"video{n}", f"📹 Тренировка {n}") for n in range(1, 5)]

# Социальные сети на главной странице: (имя иконки, подпись, ссылка).
# ЗАМЕНИТЕ ссылки на свои. Если ссылка пустая ("") — кнопка не показывается.
# Логотип берётся из static/icons/<имя>.svg (одноцветный SVG).
# Если файла нет — вместо него показывается эмодзи из SOCIAL_FALLBACK.
SOCIALS = [
    ("telegram", "Telegram-канал", "https://t.me/maleinasamokhinfan"),
    ("vk", "Группа ВКонтакте", "https://vk.com/clubmaleina_samokhinfan"),
    ("instagram", "Instagram", "https://www.instagram.com/"),
    ("max", "Группа MAX", "https://max.ru/join/3AOGjZCMbVi2NN6cS1dGF5xKE0xCBzFj5VRESDpnprg"),
]

SOCIAL_FALLBACK = {"telegram": "✈️", "vk": "👥", "instagram": "📷", "max": "💬"}

ACHIEVEMENTS = [
    ("🥈", "Серебряные призёры первенства (чемпионата) России среди юниоров 2025 года"),
    ("🥉", "Бронзовые призёры первенства (чемпионата) России среди юниоров 2026 года"),
    ("🥇", "Чемпионы Российско-китайских юношеских игр 2024 года"),
    ("🥇🥈🥉", "Победители и призёры этапов Гран-при России среди юниоров"),
    ("🥇", "Победители соревнований в рамках Кубка Первого канала (произвольный танец)"),
]

BACK_BUTTON = (
    '<div class="nav-buttons"><a href="/" class="neon-btn">← Вернуться назад</a></div>'
)


# ============================================================
# ОБЩИЙ CSS (один раз, вместо дублирования в каждом шаблоне)
# ============================================================

BASE_CSS = """
:root {
    --serif: Georgia, "Times New Roman", serif;
    --bg: linear-gradient(rgba(10,10,30,.35), rgba(10,10,30,.35)),
          url('/static/images/1.jpg') center/cover no-repeat;
}

* { box-sizing: border-box; }

body {
    margin: 0;
    font-family: "Segoe UI", Arial, sans-serif;
    background-color: var(--bgc, #0d0d1a);
    color: #fff;
}

/* Фон вынесен в fixed-слой: нет перерисовки при скролле
   (background-attachment: fixed тормозит, особенно на телефонах) */
body::before {
    content: "";
    position: fixed;
    inset: 0;
    z-index: -1;
    pointer-events: none;
    background: var(--bg);
}

body.center {
    min-height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 20px;
}

.container {
    position: relative;
    z-index: 2;
    width: 100%;
    text-align: center;
    border-radius: 25px;
    backdrop-filter: blur(15px);
}

.container.scroll { max-height: 90vh; overflow-y: auto; }

h2 {
    margin: 0 0 30px;
    color: #0ff;
    font-size: 36px;
    text-shadow: 0 0 15px #0ff;
}

h2, .subtitle, .video-card h3, .play-btn, .fullscreen-btn, .neon-btn,
.info-title, .info-text, .achievements-list li, .photo-caption, .source-credit {
    font-family: var(--serif);
    font-style: italic;
}

.nav-buttons {
    display: flex;
    gap: 15px;
    justify-content: center;
    flex-wrap: wrap;
    margin-top: 30px;
}

/* Неоновая кнопка */
.neon-btn {
    display: inline-block;
    width: 455px;
    max-width: 100%;
    padding: 16px 20px;
    color: #0ff;
    border: 2px solid #0ff;
    border-radius: 30px;
    background: rgba(52,40,95,.85);
    font-size: 22px;
    letter-spacing: 1px;
    text-decoration: none;
    text-align: center;
    white-space: nowrap;
    cursor: pointer;
    backdrop-filter: blur(8px);
    box-shadow: 0 0 15px rgba(0,255,255,.3), inset 0 0 10px rgba(0,255,255,.1);
    transition: transform .3s, background .3s, color .3s, box-shadow .3s;
}

.neon-btn:hover {
    transform: translateY(-3px) scale(1.05);
    background: #0ff;
    color: #000;
    box-shadow: 0 0 30px rgba(0,255,255,.6), 0 0 50px rgba(0,255,255,.3);
}

.neon-btn:active { transform: scale(.97); }

@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after { animation: none !important; transition: none !important; }
}
"""


# ============================================================
# CSS ОТДЕЛЬНЫХ СТРАНИЦ
# ============================================================

HOME_CSS = """
html, body { width: 100%; min-height: 100%; }

body {
    --bgc: #dce9f5;
    --bg: linear-gradient(90deg, rgba(225,225,245,.18) 0%, rgba(220,225,245,.08) 35%, rgba(0,0,0,0) 65%),
          url('/static/images/FONGLAV.png') center/cover no-repeat;
    overflow-x: hidden;
}

body::after {
    content: "";
    position: fixed;
    inset: 0;
    pointer-events: none;
    background: radial-gradient(circle at 20% 35%, rgba(255,255,255,.22), transparent 35%);
}

.hero {
    min-height: 100vh;
    position: relative;
    display: flex;
    align-items: flex-end;
    padding: 0 7% 6%;
}

.fan-title-container {
    position: absolute;
    top: 8%;
    left: 7%;
    z-index: 100;
    text-align: left;
    max-width: 800px;
    animation: title-appear 1.5s ease-out;
}

.fan-title {
    font-size: clamp(80px, 10vw, 140px);
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 10px;
    margin: 0;
    line-height: 1;
    color: #27204f;
    text-shadow: 0 2px 4px rgba(255,255,255,.9),
                 0 5px 18px rgba(50,35,110,.45),
                 0 0 30px rgba(255,255,255,.35);
    animation: title-appear 1.5s ease-out;
}

.fan-line {
    width: 220px;
    height: 3px;
    margin: 25px 0;
    background: linear-gradient(90deg, #34285f, rgba(52,40,95,.5), rgba(52,40,95,0));
    box-shadow: 0 0 8px rgba(50,40,100,.35);
}

.fan-subtitle {
    font-size: clamp(28px, 3vw, 48px);
    line-height: 1.2;
    letter-spacing: 1px;
    font-family: var(--serif);
    font-style: italic;
    color: #34285f;
    text-shadow: 0 2px 3px rgba(255,255,255,.95), 0 4px 12px rgba(60,45,120,.35);
    margin: 0;
}

.fan-subtitle .and {
    display: block;
    font-size: 24px;
    margin: 12px 0;
    letter-spacing: 7px;
    font-style: normal;
    color: #514477;
    text-shadow: 0 1px 3px rgba(255,255,255,.9);
}

.fan-description {
    margin-top: 30px;
    font-size: 18px;
    line-height: 1.6;
    letter-spacing: 1.5px;
    color: #302752;
    text-shadow: 0 1px 3px rgba(255,255,255,.9);
    max-width: 550px;
}

.hero-buttons {
    margin-top: 40px;
    display: flex;
    flex-direction: column;
    gap: 15px;
    align-items: flex-start;
}

.social { margin-top: 15px; }

.social-title {
    margin: 0 0 10px;
    font-family: var(--serif);
    font-style: italic;
    font-size: 18px;
    letter-spacing: 1px;
    color: #34285f;
    text-shadow: 0 1px 3px rgba(255,255,255,.9);
}

.social-links {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    width: 455px;
    max-width: 100%;
}

/* Логотип рисуется маской: берёт цвет текста кнопки (бирюзовый, при наведении чёрный) */
.social-ico {
    display: inline-block;
    width: 1.15em;
    height: 1.15em;
    vertical-align: -.2em;
    margin-right: 6px;
    background: currentColor;
    -webkit-mask: var(--ico) center/contain no-repeat;
    mask: var(--ico) center/contain no-repeat;
}

.neon-btn.social-btn {
    width: 100%;
    padding: 11px 12px;
    font-size: 17px;
    letter-spacing: .5px;
}

.site-signature {
    position: absolute;
    bottom: 25px;
    left: 7%;
    color: rgba(45,35,85,.55);
    font-size: 12px;
    letter-spacing: 2px;
    text-shadow: 0 1px 2px rgba(255,255,255,.8);
}

.snow-decoration, .ice-star { position: absolute; pointer-events: none; }

.snow-decoration {
    left: 3%;
    top: 5%;
    color: rgba(255,255,255,.75);
    font-size: 50px;
    text-shadow: 0 0 15px #fff, 0 0 30px rgba(160,140,255,.7);
    animation: snow-float 5s ease-in-out infinite;
}

.snow-decoration.second {
    left: 42%;
    top: 78%;
    font-size: 32px;
    opacity: .55;
    animation-delay: 2s;
}

.ice-star {
    color: rgba(255,255,255,.85);
    text-shadow: 0 0 15px #fff, 0 0 30px rgba(180,160,255,.8);
}

.star1 { top: 18%; left: 48%; font-size: 22px; animation: float1 4s ease-in-out infinite; }
.star2 { top: 67%; left: 44%; font-size: 16px; animation: float2 5s ease-in-out infinite; }
.star3 { top: 13%; right: 7%; font-size: 18px; animation: float1 6s ease-in-out infinite; }

@keyframes title-appear {
    from { opacity: 0; transform: translateX(-40px); }
    to   { opacity: 1; transform: translateX(0); }
}

@keyframes snow-float {
    0%, 100% { transform: translateY(0) rotate(0deg); }
    50%      { transform: translateY(-12px) rotate(12deg); }
}

@keyframes float1 {
    0%, 100% { transform: translateY(0) rotate(0deg); }
    50%      { transform: translateY(-15px) rotate(20deg); }
}

@keyframes float2 {
    0%, 100% { transform: translateY(0); }
    50%      { transform: translateY(12px); }
}

@media (max-width: 768px) {
    body {
        --bg: linear-gradient(90deg, rgba(220,220,245,.35), rgba(220,220,245,.1)),
              url('/static/images/FONGLAV.png') 62% center/cover no-repeat;
    }
    .hero { padding: 30px 25px 60px; align-items: flex-start; }
    .fan-title-container {
        position: relative;
        top: auto;
        left: auto;
        margin-top: 5vh;
        max-width: 100%;
    }
    .fan-title { font-size: 52px; letter-spacing: 5px; }
    .fan-subtitle { font-size: 30px; }
    .fan-description { font-size: 15px; max-width: 330px; }
    .site-signature { left: 25px; }
    .snow-decoration { display: none; }
    .neon-btn { width: 100%; font-size: 20px; }
    .social-links { width: 100%; gap: 10px; }
    .neon-btn.social-btn { font-size: 15px; padding: 10px 6px; letter-spacing: 0; white-space: normal; }
}
"""

VIDEOS_CSS = """
body { padding: 30px; min-height: 100vh; }

.container {
    background: rgba(13,13,26,.72);
    padding: 40px;
    max-width: 1400px;
    margin: 0 auto;
    box-shadow: 0 0 50px rgba(120,100,255,.25);
    border: 1px solid rgba(255,255,255,.18);
}

h2 { color: #fff; font-size: 38px; margin-bottom: 10px; text-shadow: 0 0 15px rgba(170,150,255,.8); }

.subtitle {
    color: rgba(220,210,255,.9);
    font-size: 18px;
    margin: 0 0 30px;
    letter-spacing: 1px;
}

/* Левая треть — главное видео, правые 2/3 — сетка 2×2 */
.videos-layout {
    display: grid;
    grid-template-columns: 1fr 2fr;
    gap: 30px;
    margin: 20px 0;
    align-items: start;
}

.videos-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 30px;
}

.videos-layout .video-card { min-width: 0; }
.videos-grid .play-btn, .videos-grid .fullscreen-btn { padding: 10px 16px; font-size: 14px; }

.video-card {
    background: rgba(0,0,0,.35);
    border: 1px solid rgba(210,200,255,.45);
    border-radius: 20px;
    padding: 20px;
    box-shadow: 0 0 25px rgba(100,80,200,.15);
    transition: transform .3s, box-shadow .3s;
}

.video-card:hover { transform: translateY(-5px); box-shadow: 0 0 35px rgba(170,150,255,.35); }

.video-card h3 {
    color: #eee7ff;
    margin: 0 0 15px;
    font-size: 19px;
    text-shadow: 0 0 10px rgba(200,180,255,.6);
}

.video-container {
    border-radius: 15px;
    overflow: hidden;
    background: #000;
    border: 1px solid rgba(220,210,255,.4);
    box-shadow: 0 0 20px rgba(100,80,200,.2);
}

.video-container video { width: 100%; display: block; background: #000; }

.video-controls {
    display: flex;
    gap: 10px;
    justify-content: center;
    flex-wrap: wrap;
    margin-top: 15px;
}

.play-btn, .fullscreen-btn {
    padding: 11px 24px;
    background: rgba(20,15,50,.75);
    color: #fff;
    border: 1px solid rgba(220,210,255,.6);
    border-radius: 25px;
    font-size: 15px;
    font-weight: 600;
    letter-spacing: .5px;
    cursor: pointer;
    transition: transform .3s, background .3s, box-shadow .3s;
}

.play-btn:hover, .fullscreen-btn:hover {
    background: rgba(210,200,255,.2);
    box-shadow: 0 0 20px rgba(190,170,255,.4);
    transform: scale(1.04);
}

.play-btn.pause { border-color: rgba(255,220,150,.8); color: #fff0cc; }

@media (min-width: 769px) and (max-width: 1024px) {
    .videos-layout, .videos-grid { gap: 15px; }
    .video-card { padding: 12px; }
}

@media (max-width: 768px) {
    body { padding: 15px; }
    .container { padding: 20px; }
    h2 { font-size: 28px; }
    .videos-layout, .videos-grid { grid-template-columns: 1fr; gap: 20px; }
    .nav-buttons { flex-direction: column; align-items: center; }
}
"""

ABOUT_CSS = """
.container {
    background: rgba(13,13,26,.85);
    padding: 50px;
    max-width: 900px;
    box-shadow: 0 0 40px rgba(100,80,200,.3);
    border: 1px solid rgba(0,255,255,.4);
}

h2 { font-size: 40px; text-shadow: 0 0 20px #0ff; }

.info-section { text-align: left; margin-bottom: 30px; }

.info-title {
    color: #ff00de;
    font-size: 24px;
    font-weight: bold;
    text-shadow: 0 0 10px rgba(255,0,222,.5);
    margin-bottom: 15px;
    border-bottom: 2px solid rgba(255,0,222,.3);
    padding-bottom: 10px;
}

.info-text, .achievements-list li {
    color: rgba(255,255,255,.9);
    line-height: 1.8;
    font-size: 18px;
}

.info-text { margin: 0; }

.achievements-list { list-style: none; padding: 0; margin: 0; }

.achievements-list li { padding: 8px 0; border-bottom: 1px solid rgba(0,255,255,.2); }
.achievements-list li:last-child { border-bottom: none; }

.achievement-medal { display: inline-block; margin-right: 10px; font-size: 20px; }

.nav-buttons { margin-top: 40px; }

@media (max-width: 768px) {
    .container { padding: 25px; }
    h2 { font-size: 30px; }
    .info-title { font-size: 20px; }
    .info-text, .achievements-list li { font-size: 16px; }
}
"""

PHOTOS_CSS = """
.container {
    background: rgba(13,13,26,.78);
    padding: 45px;
    max-width: 1200px;
    box-shadow: 0 0 40px rgba(100,80,200,.3);
    border: 1px solid rgba(0,255,255,.5);
}

.photos-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 25px;
    margin-bottom: 30px;
}

.photo-card {
    background: rgba(0,0,0,.4);
    border: 2px solid rgba(0,255,255,.4);
    border-radius: 15px;
    overflow: hidden;
    box-shadow: 0 0 25px rgba(0,255,255,.2);
    transition: transform .3s, box-shadow .3s, border-color .3s;
    cursor: pointer;
}

.photo-card:hover, .photo-card:focus-visible {
    transform: translateY(-5px) scale(1.02);
    box-shadow: 0 0 40px rgba(0,255,255,.5);
    border-color: #0ff;
    outline: none;
}

.photo-card img { width: 100%; height: 250px; object-fit: cover; display: block; }

.photo-caption { padding: 12px; color: #0ff; font-size: 14px; text-align: center; }

.source-credit {
    margin-top: 30px;
    padding: 15px;
    color: rgba(255,255,255,.6);
    font-size: 14px;
    border-top: 1px solid rgba(255,255,255,.2);
}

.source-credit a {
    color: #0ff;
    text-decoration: none;
    transition: color .3s, text-shadow .3s;
    text-shadow: 0 0 10px rgba(0,255,255,.5);
}

.source-credit a:hover { color: #ff00de; text-shadow: 0 0 15px rgba(255,0,222,.7); }

.modal {
    display: none;
    position: fixed;
    inset: 0;
    z-index: 1000;
    background: rgba(0,0,0,.95);
    justify-content: center;
    align-items: center;
    cursor: zoom-out;
}

.modal.active { display: flex; }

.modal img {
    max-width: 95%;
    max-height: 95%;
    object-fit: contain;
    border: 2px solid rgba(0,255,255,.5);
    border-radius: 10px;
    box-shadow: 0 0 50px rgba(0,255,255,.3);
    animation: zoomIn .3s ease;
}

@keyframes zoomIn {
    from { transform: scale(.5); opacity: 0; }
    to   { transform: scale(1);  opacity: 1; }
}

.modal-close {
    position: absolute;
    top: 20px;
    right: 30px;
    color: #0ff;
    font-size: 40px;
    font-weight: bold;
    cursor: pointer;
    text-shadow: 0 0 10px rgba(0,255,255,.8);
    transition: transform .3s, color .3s, text-shadow .3s;
}

.modal-close:hover { transform: scale(1.2); color: #ff00de; text-shadow: 0 0 20px rgba(255,0,222,.8); }

@media (min-width: 769px) and (max-width: 1024px) {
    .photos-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 768px) {
    .container { padding: 25px; }
    h2 { font-size: 28px; }
    .photos-grid { grid-template-columns: 1fr; gap: 20px; }
    .modal-close { top: 10px; right: 20px; font-size: 30px; }
}
"""


# ============================================================
# JAVASCRIPT
# ============================================================

VIDEOS_JS = """
(function () {
    var grid = document.querySelector('.videos-layout');
    var videos = grid.querySelectorAll('video');

    function setLabel(video, playing) {
        var btn = video.closest('.video-card').querySelector('.play-btn');
        btn.textContent = playing ? '⏸ Пауза' : '▶ Воспроизвести';
        btn.classList.toggle('pause', playing);
    }

    grid.addEventListener('click', function (e) {
        var btn = e.target.closest('button[data-action]');
        if (!btn) return;
        var video = btn.closest('.video-card').querySelector('video');

        if (btn.dataset.action === 'fullscreen') {
            var fs = video.requestFullscreen || video.webkitRequestFullscreen || video.msRequestFullscreen;
            if (fs) fs.call(video);
        } else if (video.paused) {
            video.play();
        } else {
            video.pause();
        }
    });

    // play/pause/ended не всплывают, поэтому вешаем на каждое видео.
    // Кнопка и «пауза остальных» работают и при нажатии на встроенные controls.
    videos.forEach(function (video) {
        video.addEventListener('play', function () {
            videos.forEach(function (other) {
                if (other !== video && !other.paused) other.pause();
            });
            setLabel(video, true);
        });
        video.addEventListener('pause', function () { setLabel(video, false); });
        video.addEventListener('ended', function () { setLabel(video, false); });
    });
})();
"""

PHOTOS_JS = """
(function () {
    var modal = document.getElementById('photoModal');
    var img = document.getElementById('modalImage');
    var grid = document.querySelector('.photos-grid');

    function openModal(src) {
        img.src = src;
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    function closeModal() {
        modal.classList.remove('active');
        img.removeAttribute('src');
        document.body.style.overflow = '';
    }

    grid.addEventListener('click', function (e) {
        var card = e.target.closest('.photo-card');
        if (card) openModal(card.dataset.full);
    });

    grid.addEventListener('keydown', function (e) {
        if (e.key !== 'Enter' && e.key !== ' ') return;
        var card = e.target.closest('.photo-card');
        if (card) { e.preventDefault(); openModal(card.dataset.full); }
    });

    modal.addEventListener('click', closeModal);
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') closeModal();
    });
})();
"""


# ============================================================
# СБОРКА СТРАНИЦ (выполняется один раз при запуске)
# ============================================================

def minify_css(css):
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = re.sub(r"\s+", " ", css)
    css = re.sub(r"\s*([{};,])\s*", r"\1", css)
    return css.strip()


def build_page(title, description, css, body, script="", body_class=""):
    cls = f' class="{body_class}"' if body_class else ""
    scr = f"<script>{script.strip()}</script>" if script else ""
    return (
        '<!DOCTYPE html><html lang="ru"><head><meta charset="UTF-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
        f'<meta name="description" content="{description}">'
        f"<title>{title}</title>"
        f"<style>{minify_css(BASE_CSS + css)}</style></head>"
        f"<body{cls}>{body}{scr}</body></html>"
    )


def home_page():
    def social_icon(name):
        svg = os.path.join(app.static_folder, "icons", f"{name}.svg")
        if os.path.exists(svg):
            # ?v=время изменения файла: при замене иконки браузер сразу берёт новую, а не кэш
            ver = int(os.path.getmtime(svg))
            return f'<span class="social-ico" style="--ico:url(/static/icons/{name}.svg?v={ver})"></span>'
        return SOCIAL_FALLBACK.get(name, "") + " "

    links = "".join(
        f'<a href="{url}" class="neon-btn social-btn" target="_blank" '
        f'rel="noopener noreferrer">{social_icon(name)}{label}</a>'
        for name, label, url in SOCIALS
        if url
    )
    social = (
        f'<div class="social"><div class="social-title">Мы в соцсетях</div>'
        f'<div class="social-links">{links}</div></div>'
        if links
        else ""
    )
    body = f"""
<div class="hero">
  <div class="ice-star star1">✦</div>
  <div class="ice-star star2">✧</div>
  <div class="ice-star star3">✦</div>
  <div class="snow-decoration">❄</div>
  <div class="snow-decoration second">❄</div>

  <div class="fan-title-container">
    <h1 class="fan-title">FAN GROUP</h1>
    <div class="fan-line"></div>
    <div class="fan-subtitle">
      Elizaveta Maleina <span class="and">AND</span> Matvey Samokhin
    </div>
    <div class="fan-description">
      Фан-сайт, посвящённый фигурному катанию, тренировкам,
      выступлениям и творчеству нашей любимой пары.
    </div>
    <div class="hero-buttons">
      <a href="/about" class="neon-btn">💑 О паре</a>
      <a href="/second" class="neon-btn">🎬 Смотреть тренировки</a>
      <a href="/photos" class="neon-btn">📸 Фотографии</a>
    </div>
    {social}
  </div>

  <div class="site-signature">FIGURE SKATING • FAN GROUP</div>
</div>
"""
    return build_page(
        "Fan Group — Elizaveta Maleina &amp; Matvey Samokhin",
        "Фан-сайт, посвящённый фигурному катанию: Елизавета Малеина и Матвей Самохин",
        HOME_CSS,
        body,
    )


# MIME-типы для <source>. Для .mov указываем video/mp4: Chrome/Edge не знают
# "video/quicktime" и пропустили бы файл, хотя H.264 внутри .mov они играют.
VIDEO_TYPES = {"mp4": "video/mp4", "webm": "video/webm", "mov": "video/mp4"}


def video_card(name, title, exts=("mp4", "webm")):
    sources = "\n      ".join(
        f'<source src="/static/videos/{name}.{e}" type="{VIDEO_TYPES[e]}">' for e in exts
    )
    return f"""
<div class="video-card">
  <h3>{title}</h3>
  <div class="video-container">
    <video loop controls playsinline preload="metadata">
      {sources}
      Ваш браузер не поддерживает тег video.
    </video>
  </div>
  <div class="video-controls">
    <button class="play-btn" data-action="toggle">▶ Воспроизвести</button>
    <button class="fullscreen-btn" data-action="fullscreen">⛶ На весь экран</button>
  </div>
</div>"""


def videos_page():
    main = video_card(*MAIN_VIDEO)
    grid = "".join(video_card(name, title) for name, title in GRID_VIDEOS)
    body = f"""
<div class="container">
  <h2>🎬 Тренировки</h2>
  <p class="subtitle">Elizaveta Maleina &amp; Matvey Samokhin</p>
  <div class="videos-layout">
    {main}
    <div class="videos-grid">{grid}</div>
  </div>
  {BACK_BUTTON}
</div>
"""
    return build_page(
        "Тренировки — Elizaveta &amp; Matvey",
        "Видео тренировок Елизаветы Малеиной и Матвея Самохина",
        VIDEOS_CSS,
        body,
        VIDEOS_JS,
    )


def about_page():
    medals = "".join(
        f'<li><span class="achievement-medal">{m}</span>{t}</li>' for m, t in ACHIEVEMENTS
    )
    body = f"""
<div class="container scroll">
  <h2>💑 О паре</h2>

  <div class="info-section">
    <p class="info-text">
      Елизавета Малеина и Матвей Самохин — российская танцевальная пара
      в фигурном катании, выступающая среди юниоров.
    </p>
  </div>

  <div class="info-section">
    <div class="info-title">🏆 Достижения пары</div>
    <ul class="achievements-list">{medals}</ul>
  </div>

  <div class="info-section">
    <div class="info-title">👥 Тренеры и штаб</div>
    <p class="info-text">
      Тренируются под руководством
      <strong>Самохина Дениса Эдуардовича</strong>,
      <strong>Боровиковой Марии Валерьевны</strong>,
      <strong>Назарова Никиты Геннадьевича</strong> и
      <strong>Никонова Николая Юрьевича</strong>.
    </p>
  </div>

  <div class="info-section">
    <div class="info-title">🏠 Представляют</div>
    <p class="info-text">
      Московскую область г. Балашиха
      (СПОРТИВНУЮ ШКОЛУ ОЛИМПИЙСКОГО РЕЗЕРВА имени Ю. Е. ЛЯПКИНА)
    </p>
  </div>

  {BACK_BUTTON}
</div>
"""
    return build_page(
        "О паре — Elizaveta &amp; Matvey",
        "О паре Елизавета Малеина и Матвей Самохин: достижения, тренеры, школа",
        ABOUT_CSS,
        body,
        body_class="center",
    )


def photos_page():
    alt = "Елизавета Малеина и Матвей Самохин"
    cards = "".join(
        f'<div class="photo-card" role="button" tabindex="0" data-full="{PHOTO_BASE}{p}">'
        f'<img src="{PHOTO_BASE}{p}" alt="{alt}" loading="lazy" decoding="async">'
        f'<div class="photo-caption">Elizaveta &amp; Matvey</div></div>'
        for p in PHOTOS
    )
    body = f"""
<div class="container scroll">
  <h2>📸 Фотографии</h2>
  <div class="photos-grid">{cards}</div>
  <div class="source-credit">
    Фото взяты с сайта
    <a href="https://figure-skaters.ru/" target="_blank" rel="noopener noreferrer">figure-skaters.ru</a>
  </div>
  {BACK_BUTTON}
</div>

<div id="photoModal" class="modal" role="dialog" aria-modal="true">
  <span class="modal-close" aria-label="Закрыть">×</span>
  <img id="modalImage" alt="Фото в полном размере">
</div>
"""
    return build_page(
        "Фотографии — Elizaveta &amp; Matvey",
        "Фотографии Елизаветы Малеиной и Матвея Самохина",
        PHOTOS_CSS,
        body,
        PHOTOS_JS,
        body_class="center",
    )


# Готовые страницы: (байты, ETag)
def _pack(html):
    data = html.encode("utf-8")
    return data, '"' + hashlib.md5(data).hexdigest() + '"'


PAGES = {
    "home": _pack(home_page()),
    "second": _pack(videos_page()),
    "about": _pack(about_page()),
    "photos": _pack(photos_page()),
}

CACHE_CONTROL = "public, max-age=300"


def serve(name):
    data, etag = PAGES[name]
    headers = {"ETag": etag, "Cache-Control": CACHE_CONTROL}
    # Браузер уже имеет актуальную копию — ничего не отправляем
    if request.headers.get("If-None-Match") == etag:
        return Response(status=304, headers=headers)
    return Response(data, mimetype="text/html", headers=headers)


# ============================================================
# МАРШРУТЫ
# ============================================================

app.add_url_rule("/", "home", lambda: serve("home"))
app.add_url_rule("/second", "second_page", lambda: serve("second"))  # видео
app.add_url_rule("/about", "about_page", lambda: serve("about"))     # о паре
app.add_url_rule("/photos", "photos_page", lambda: serve("photos"))  # фото


# ============================================================
# ЗАПУСК
# ============================================================

if __name__ == "__main__":
    # debug=True на 0.0.0.0 открывает отладчик Werkzeug (удалённое выполнение кода),
    # поэтому он включается только явно: FLASK_DEBUG=1 python ag6_optimized.py
    debug = os.environ.get("FLASK_DEBUG") == "1"
    app.run(host="127.0.0.1" if debug else "0.0.0.0", port=5000, debug=debug)