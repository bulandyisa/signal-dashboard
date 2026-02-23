"""
СИГНАЛ — Production Dashboard
Streamlit-дашборд для анимационного проекта
"""

import json
import os
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent
PROMPTS_FILE = BASE_DIR / "output" / "prompts" / "all_prompts.json"
FRAMES_DIR = BASE_DIR / "output" / "frames"
CLIPS_DIR = BASE_DIR / "output" / "clips"
SCENE_DIR = BASE_DIR / "output" / "scene"
CHARS_DIR = BASE_DIR / "characters"
LOCS_DIR = BASE_DIR / "locations"
SCENARIO_FILE = BASE_DIR / "scenario_signal.txt"

SCENE_COLORS = {
    "S01": "#E8B849",  # gold
    "S02": "#49B6E8",  # blue
    "S03": "#E85A49",  # red
    "S04": "#6BE849",  # green
    "S05": "#C149E8",  # purple
}

SCENE_LABELS = {
    "S01": "Сцена 1 — Холодное открытие",
    "S02": "Сцена 2 — Гараж, 4 дня назад",
    "S03": "Сцена 3 — Дом Амина, вечер",
    "S04": "Сцена 4 — Гараж, 3 дня назад",
    "S05": "Сцена 5 — Гараж, вечер",
}

CHAR_DISPLAY = {
    "Amin": "Амин",
    "Karim": "Карим",
    "Tako": "Тако",
    "Papa": "Папа",
    "Mama": "Мама",
    "Aya": "Ая",
    "Hasan": "Хасан",
    "Rami": "Рами",
    "Samir": "Самир",
    "Shaki": "Шаки",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@st.cache_data
def load_clips() -> list[dict]:
    """Load clip data from all_prompts.json."""
    with open(PROMPTS_FILE, encoding="utf-8") as f:
        return json.load(f)


def get_status(clip_id: str) -> str:
    """Determine clip status based on existing output files."""
    has_first = (FRAMES_DIR / f"{clip_id}_first.png").exists()
    has_last = (FRAMES_DIR / f"{clip_id}_last.png").exists()
    has_clip = (CLIPS_DIR / f"{clip_id}_clip.mp4").exists()

    if has_first and has_last and has_clip:
        return "done"
    elif has_first or has_last or has_clip:
        return "partial"
    return "todo"


STATUS_MAP = {
    "done": ("Готово", "🟢"),
    "partial": ("Частично", "🟡"),
    "todo": ("Не начато", "🔴"),
}


def scene_badge(scene_id: str) -> str:
    """Return HTML badge for a scene."""
    color = SCENE_COLORS.get(scene_id, "#888")
    return (
        f'<span style="background:{color};color:#000;padding:2px 8px;'
        f'border-radius:4px;font-weight:600;font-size:0.85em;">{scene_id}</span>'
    )


def download_button_for_file(filepath: Path, label: str, key: str):
    """Render a download button if file exists."""
    if filepath.exists():
        data = filepath.read_bytes()
        suffix = filepath.suffix.lstrip(".")
        mime = "image/png" if suffix == "png" else f"video/{suffix}"
        st.download_button(label, data, file_name=filepath.name, mime=mime, key=key)


def char_thumbnail(char_name: str, size: int = 60) -> str | None:
    """Find a character reference image for thumbnail."""
    name_lower = char_name.lower()
    for pattern in [f"char_{name_lower}_full*", f"char_{name_lower}_face*"]:
        matches = list(CHARS_DIR.glob(pattern))
        if matches:
            return str(matches[0])
    return None


def loc_thumbnail(location: str) -> str | None:
    """Find a location reference image for thumbnail."""
    loc_map = {
        "Garage": "loc_garazh_inside",
        "Amin room": "loc_amin_room_full",
        "Papa office": "loc_kabinet_full",
    }
    key = loc_map.get(location, "")
    if key:
        matches = list(LOCS_DIR.glob(f"{key}*"))
        if matches:
            return str(matches[0])
    return None


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

def inject_css():
    st.markdown("""
    <style>
    /* Global */
    .block-container { max-width: 1200px; }

    /* Scene badge */
    .scene-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 4px;
        font-weight: 700;
        font-size: 0.85em;
        color: #000;
    }

    /* Clip card */
    .clip-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 4px;
    }
    .clip-header h3 { margin: 0; }

    /* Status pill */
    .status-pill {
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.8em;
        font-weight: 600;
    }
    .status-done { background: #1B5E20; color: #A5D6A7; }
    .status-partial { background: #E65100; color: #FFE0B2; }
    .status-todo { background: #B71C1C; color: #FFCDD2; }

    /* Prompt blocks */
    .prompt-block {
        background: #1A1D26;
        border-left: 3px solid #E8B849;
        padding: 10px 14px;
        border-radius: 0 6px 6px 0;
        margin: 6px 0;
        font-size: 0.9em;
        line-height: 1.5;
    }
    .prompt-label {
        color: #E8B849;
        font-weight: 700;
        font-size: 0.78em;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }

    /* Ref gallery */
    .ref-gallery {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
    }
    .ref-card {
        text-align: center;
        font-size: 0.78em;
        color: #aaa;
    }
    .ref-card img {
        border-radius: 6px;
        border: 1px solid #333;
    }

    /* Stats */
    .stat-card {
        background: #1A1D26;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
    }
    .stat-card .number {
        font-size: 2em;
        font-weight: 700;
        color: #E8B849;
    }
    .stat-card .label {
        font-size: 0.85em;
        color: #999;
    }

    /* Ingredient role badge */
    .role-badge {
        display: inline-block;
        background: #2A2D36;
        padding: 1px 6px;
        border-radius: 3px;
        font-size: 0.72em;
        color: #bbb;
    }

    /* Mobile */
    @media (max-width: 768px) {
        .block-container { padding: 0.5rem 1rem; }
    }
    </style>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

def page_clips():
    """Main clips dashboard page."""
    clips = load_clips()

    # --- Sidebar filters ---
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Фильтры")

    # Scene filter
    scene_ids = sorted(set(c["scene_id"] for c in clips))
    scene_options = ["Все"] + scene_ids
    selected_scene = st.sidebar.selectbox("Сцена", scene_options)

    # Status filter
    status_options = ["Все", "Готово", "Частично", "Не начато"]
    selected_status = st.sidebar.selectbox("Статус", status_options)

    # Character filter
    all_chars = sorted(set(ch for c in clips for ch in c["characters"]))
    selected_char = st.sidebar.selectbox(
        "Персонаж", ["Все"] + all_chars,
        format_func=lambda x: CHAR_DISPLAY.get(x, x) if x != "Все" else "Все"
    )

    # --- Apply filters ---
    filtered = clips
    if selected_scene != "Все":
        filtered = [c for c in filtered if c["scene_id"] == selected_scene]
    if selected_status != "Все":
        status_key = {"Готово": "done", "Частично": "partial", "Не начато": "todo"}[selected_status]
        filtered = [c for c in filtered if get_status(c["clip_id"]) == status_key]
    if selected_char != "Все":
        filtered = [c for c in filtered if selected_char in c["characters"]]

    # --- Sidebar stats ---
    st.sidebar.markdown("---")
    all_statuses = [get_status(c["clip_id"]) for c in clips]
    done_count = all_statuses.count("done")
    partial_count = all_statuses.count("partial")
    total = len(clips)
    st.sidebar.markdown(f"**Готово:** {done_count}/{total} клипов")
    st.sidebar.markdown(f"**Частично:** {partial_count}/{total} клипов")
    st.sidebar.progress(done_count / total if total else 0)

    # --- Overview stats ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""<div class="stat-card">
            <div class="number">{total}</div>
            <div class="label">Всего клипов</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="stat-card">
            <div class="number">{len(scene_ids)}</div>
            <div class="label">Сцен</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div class="stat-card">
            <div class="number">{done_count}</div>
            <div class="label">🟢 Готово</div>
        </div>""", unsafe_allow_html=True)
    with col4:
        total_dur = sum(c.get("veo_duration", 0) for c in clips)
        st.markdown(f"""<div class="stat-card">
            <div class="number">{total_dur}с</div>
            <div class="label">Общая длительность</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("")

    # --- Clip cards ---
    if not filtered:
        st.info("Нет клипов по выбранным фильтрам.")
        return

    current_scene = None
    for clip in filtered:
        # Scene header
        if clip["scene_id"] != current_scene:
            current_scene = clip["scene_id"]
            color = SCENE_COLORS.get(current_scene, "#888")
            label = SCENE_LABELS.get(current_scene, current_scene)
            st.markdown(
                f'<h3 style="border-bottom:2px solid {color};padding-bottom:6px;'
                f'margin-top:24px;">{label}</h3>',
                unsafe_allow_html=True,
            )

        status = get_status(clip["clip_id"])
        status_label, status_icon = STATUS_MAP[status]
        status_class = f"status-{status}"

        # Expander per clip
        header_text = (
            f'{status_icon} {clip["clip_id"]} — {clip["scene_description_ru"]}'
        )
        with st.expander(header_text, expanded=False):
            render_clip_card(clip, status, status_label, status_class)


def render_clip_card(clip: dict, status: str, status_label: str, status_class: str):
    """Render the full clip card inside an expander."""
    clip_id = clip["clip_id"]

    # --- Row 1: Status + Meta ---
    meta_col1, meta_col2, meta_col3, meta_col4 = st.columns([1, 1, 1, 1])
    with meta_col1:
        st.markdown(
            f'<span class="status-pill {status_class}">{status_label}</span>',
            unsafe_allow_html=True,
        )
    with meta_col2:
        chars_display = ", ".join(CHAR_DISPLAY.get(c, c) for c in clip["characters"])
        st.markdown(f"**Персонажи:** {chars_display}")
    with meta_col3:
        st.markdown(f"**Локация:** {clip['location']}")
    with meta_col4:
        st.markdown(f"**Время:** {clip['time_of_day']}")

    st.markdown("---")

    # --- Row 2: Character & location thumbnails ---
    st.markdown("**Референсы (ингредиенты)**")
    ingredients = clip.get("nano_banana_ingredient_roles", [])
    if ingredients:
        cols = st.columns(min(len(ingredients), 4))
        for i, ing in enumerate(ingredients):
            filepath = BASE_DIR / ing["file"]
            with cols[i % len(cols)]:
                if filepath.exists():
                    st.image(str(filepath), width=120)
                role = ing.get("role", "")
                fname = Path(ing["file"]).name
                st.markdown(
                    f'<span class="role-badge">{role}</span><br>'
                    f'<span style="font-size:0.72em;color:#666;">{fname}</span>',
                    unsafe_allow_html=True,
                )

    st.markdown("---")

    # --- Row 3: Prompts ---
    st.markdown("**Промпты**")

    st.markdown('<div class="prompt-label">Nano Banana — First Frame</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="prompt-block">{clip["nano_banana_prompt_first"]}</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="prompt-label">Nano Banana — Last Frame</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="prompt-block">{clip["nano_banana_prompt_last"]}</div>',
        unsafe_allow_html=True,
    )

    veo_info = f'{clip["veo_duration"]}с | {clip["veo_aspect_ratio"]} | {clip["veo_model"]}'
    st.markdown(f'<div class="prompt-label">VEO — Video ({veo_info})</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="prompt-block">{clip["veo_prompt"]}</div>',
        unsafe_allow_html=True,
    )

    if clip.get("audio_note"):
        st.markdown(f'<div class="prompt-label">Audio</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="prompt-block">{clip["audio_note"]}</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # --- Row 4: Generated frames ---
    st.markdown("**Сгенерированные кадры**")
    first_frame = FRAMES_DIR / f"{clip_id}_first.png"
    last_frame = FRAMES_DIR / f"{clip_id}_last.png"

    fcol1, fcol2 = st.columns(2)
    with fcol1:
        if first_frame.exists():
            st.image(str(first_frame), caption="First frame", use_container_width=True)
            download_button_for_file(first_frame, "Скачать first frame", f"dl_first_{clip_id}")
        else:
            st.markdown(
                '<div style="background:#1A1D26;border:1px dashed #333;border-radius:8px;'
                'padding:40px;text-align:center;color:#555;">First frame — не сгенерирован</div>',
                unsafe_allow_html=True,
            )
    with fcol2:
        if last_frame.exists():
            st.image(str(last_frame), caption="Last frame", use_container_width=True)
            download_button_for_file(last_frame, "Скачать last frame", f"dl_last_{clip_id}")
        else:
            st.markdown(
                '<div style="background:#1A1D26;border:1px dashed #333;border-radius:8px;'
                'padding:40px;text-align:center;color:#555;">Last frame — не сгенерирован</div>',
                unsafe_allow_html=True,
            )

    # --- Row 5: Video ---
    st.markdown("**Видео**")
    clip_video = CLIPS_DIR / f"{clip_id}_clip.mp4"
    if clip_video.exists():
        st.video(str(clip_video))
        download_button_for_file(clip_video, "Скачать видео", f"dl_video_{clip_id}")
    else:
        st.markdown(
            '<div style="background:#1A1D26;border:1px dashed #333;border-radius:8px;'
            'padding:40px;text-align:center;color:#555;">Видео — не сгенерировано</div>',
            unsafe_allow_html=True,
        )


def page_scenario():
    """Scenario page — full script text."""
    st.header("Сценарий")

    if SCENARIO_FILE.exists():
        text = SCENARIO_FILE.read_text(encoding="utf-8")
        # Split into scenes for better navigation
        st.download_button(
            "Скачать сценарий",
            text.encode("utf-8"),
            file_name="scenario_signal.txt",
            mime="text/plain",
            key="dl_scenario",
        )
        st.markdown("---")

        # Try to split by scene markers (INT./EXT. or numbered scenes)
        lines = text.split("\n")
        current_block = []
        blocks = []
        for line in lines:
            # Detect scene headers (lines that are all caps or start with INT./EXT.)
            stripped = line.strip()
            if stripped and (
                stripped.startswith("СЦЕНА")
                or stripped.startswith("INT.")
                or stripped.startswith("EXT.")
                or (stripped.isupper() and len(stripped) > 10)
            ):
                if current_block:
                    blocks.append("\n".join(current_block))
                current_block = [line]
            else:
                current_block.append(line)
        if current_block:
            blocks.append("\n".join(current_block))

        if len(blocks) > 1:
            for block in blocks:
                first_line = block.strip().split("\n")[0].strip()
                if first_line:
                    with st.expander(first_line[:80], expanded=False):
                        st.text(block)
        else:
            st.text(text)
    else:
        st.warning("Файл сценария не найден (scenario_signal.txt)")


def page_references():
    """Reference gallery — characters and locations."""
    st.header("Референсы")

    tab_chars, tab_locs = st.tabs(["Персонажи", "Локации"])

    with tab_chars:
        st.subheader("Персонажи")
        if CHARS_DIR.exists():
            files = sorted(CHARS_DIR.glob("char_*"))
            if files:
                # Group by character name
                groups: dict[str, list[Path]] = {}
                for f in files:
                    # Extract character name: char_amin_full.png -> amin
                    parts = f.stem.split("_")
                    if len(parts) >= 2:
                        char_key = parts[1]  # e.g. "amin", "karim"
                        groups.setdefault(char_key, []).append(f)

                for char_key in sorted(groups):
                    display_name = CHAR_DISPLAY.get(
                        char_key.capitalize(), char_key.capitalize()
                    )
                    st.markdown(f"#### {display_name}")
                    char_files = groups[char_key]
                    cols = st.columns(min(len(char_files), 4))
                    for i, fpath in enumerate(char_files):
                        with cols[i % len(cols)]:
                            st.image(str(fpath), caption=fpath.name, use_container_width=True)
            else:
                st.info("Нет файлов персонажей.")
        else:
            st.warning("Папка персонажей не найдена.")

    with tab_locs:
        st.subheader("Локации")
        if LOCS_DIR.exists():
            files = sorted(LOCS_DIR.glob("loc_*"))
            if files:
                # Group by location name
                groups: dict[str, list[Path]] = {}
                for f in files:
                    parts = f.stem.split("_")
                    if len(parts) >= 2:
                        loc_key = parts[1]  # e.g. "garazh", "amin", "kabinet"
                        groups.setdefault(loc_key, []).append(f)

                loc_display = {
                    "garazh": "Гараж",
                    "amin": "Комната Амина",
                    "kabinet": "Кабинет Папы",
                    "besedka": "Беседка",
                    "dom": "Дом (экстерьер)",
                }
                for loc_key in sorted(groups):
                    display_name = loc_display.get(loc_key, loc_key.capitalize())
                    st.markdown(f"#### {display_name}")
                    loc_files = groups[loc_key]
                    cols = st.columns(min(len(loc_files), 4))
                    for i, fpath in enumerate(loc_files):
                        with cols[i % len(cols)]:
                            st.image(str(fpath), caption=fpath.name, use_container_width=True)
            else:
                st.info("Нет файлов локаций.")
        else:
            st.warning("Папка локаций не найдена.")


def page_timeline():
    """Visual timeline of all clips."""
    st.header("Таймлайн")

    clips = load_clips()
    current_scene = None

    for clip in clips:
        if clip["scene_id"] != current_scene:
            current_scene = clip["scene_id"]
            color = SCENE_COLORS.get(current_scene, "#888")
            label = SCENE_LABELS.get(current_scene, current_scene)
            st.markdown(
                f'<h4 style="color:{color};margin-top:20px;">{label}</h4>',
                unsafe_allow_html=True,
            )

        clip_id = clip["clip_id"]
        status = get_status(clip_id)
        _, status_icon = STATUS_MAP[status]
        dur = clip.get("veo_duration", 0)
        chars = ", ".join(CHAR_DISPLAY.get(c, c) for c in clip["characters"])

        # Timeline row
        cols = st.columns([1, 3, 1, 1])
        with cols[0]:
            st.markdown(f"**{status_icon} {clip_id}**")
        with cols[1]:
            st.markdown(clip["scene_description_ru"])
        with cols[2]:
            st.markdown(f"{chars}")
        with cols[3]:
            st.markdown(f"{dur}с")

        # Show frames inline if they exist
        first_frame = FRAMES_DIR / f"{clip_id}_first.png"
        last_frame = FRAMES_DIR / f"{clip_id}_last.png"
        if first_frame.exists() or last_frame.exists():
            thumb_cols = st.columns([1, 2, 2, 1])
            with thumb_cols[1]:
                if first_frame.exists():
                    st.image(str(first_frame), width=200, caption="First")
            with thumb_cols[2]:
                if last_frame.exists():
                    st.image(str(last_frame), width=200, caption="Last")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    st.set_page_config(
        page_title="СИГНАЛ — Dashboard",
        page_icon="📡",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    inject_css()

    # --- Sidebar header ---
    st.sidebar.markdown(
        '<h1 style="text-align:center;color:#E8B849;">📡 СИГНАЛ</h1>'
        '<p style="text-align:center;color:#888;font-size:0.85em;">'
        'Production Dashboard</p>',
        unsafe_allow_html=True,
    )

    # --- Navigation ---
    page = st.sidebar.radio(
        "Навигация",
        ["Клипы", "Таймлайн", "Сценарий", "Референсы"],
        label_visibility="collapsed",
    )

    # --- Page routing ---
    if page == "Клипы":
        st.title("Клипы")
        page_clips()
    elif page == "Таймлайн":
        page_timeline()
    elif page == "Сценарий":
        page_scenario()
    elif page == "Референсы":
        page_references()

    # --- Footer ---
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        '<p style="text-align:center;color:#555;font-size:0.75em;">'
        'СИГНАЛ / Signal<br>3D Pixar-style Animation<br>'
        'Nano Banana Pro + VEO 3.1</p>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
