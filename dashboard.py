"""
Путь Амина — Production Dashboard
Streamlit-дашборд для анимационного проекта (мульти-серии)
"""

import json
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent
SERIES_DIR = BASE_DIR / "series"
CHARS_DIR = BASE_DIR / "characters"
LOCS_DIR = BASE_DIR / "locations"

INGREDIENT_PATH_MAP = {
    "персонажи/": "characters/",
    "локации/": "locations/",
}


# ---------------------------------------------------------------------------
# Series discovery
# ---------------------------------------------------------------------------

@st.cache_data
def discover_series() -> dict[str, dict]:
    """Scan series/ directory and return {id: meta_dict} for each valid series."""
    result = {}
    if not SERIES_DIR.exists():
        return result
    for d in sorted(SERIES_DIR.iterdir()):
        meta_file = d / "meta.json"
        if d.is_dir() and meta_file.exists():
            with open(meta_file, encoding="utf-8") as f:
                meta = json.load(f)
            meta["_dir"] = str(d)
            result[meta["id"]] = meta
    return result


def series_paths(series_dir_str: str) -> dict[str, Path]:
    """Return standard paths for a series directory."""
    d = Path(series_dir_str)
    return {
        "prompts": d / "prompts.json",
        "frames": d / "frames",
        "clips": d / "clips",
        "scenario": d / "scenario.txt",
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@st.cache_data
def load_clips(prompts_file: str) -> list[dict]:
    """Load clip data from a prompts JSON file."""
    p = Path(prompts_file)
    if not p.exists():
        return []
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def get_video_variants(clip_id: str, clips_dir: Path) -> dict[str, list[Path]]:
    """Find all video variants for a clip. Returns {'prompt_a': [...], 'prompt_b': [...]}."""
    result = {"prompt_a": [], "prompt_b": []}
    clip_dir = clips_dir / clip_id
    if clip_dir.is_dir():
        for key in ("prompt_a", "prompt_b"):
            sub = clip_dir / key
            if sub.is_dir():
                result[key] = sorted(sub.glob("*.mp4"))
    # Backward compat: old single-file format
    old_clip = clips_dir / f"{clip_id}_clip.mp4"
    if old_clip.exists() and not result["prompt_a"] and not result["prompt_b"]:
        result["prompt_a"] = [old_clip]
    return result


def get_status(clip_id: str, frames_dir: Path, clips_dir: Path) -> str:
    """Determine clip status based on existing output files."""
    has_first = (frames_dir / f"{clip_id}_first.png").exists()
    has_last = (frames_dir / f"{clip_id}_last.png").exists()
    variants = get_video_variants(clip_id, clips_dir)
    has_videos = bool(variants["prompt_a"] or variants["prompt_b"])

    if has_videos:
        return "done"
    elif has_first or has_last:
        return "partial"
    return "todo"


STATUS_MAP = {
    "done": ("Готово", "🟢"),
    "partial": ("Частично", "🟡"),
    "todo": ("Не начато", "🔴"),
}


@st.cache_data
def load_scenario_by_scene(scenario_file: str) -> dict[str, str]:
    """Parse scenario file and return {scene_id: full_text} mapping.

    Maps scene numbers (СЦЕНА 1, СЦЕНА 2, ...) to scene IDs (S01, S02, ...).
    """
    import re
    p = Path(scenario_file)
    if not p.exists():
        return {}
    text = p.read_text(encoding="utf-8")
    scenes: dict[str, str] = {}
    # Split by scene headers like "СЦЕНА 1 — ..."
    parts = re.split(r"(?=^СЦЕНА\s+\d+)", text, flags=re.MULTILINE)
    for part in parts:
        part = part.strip()
        m = re.match(r"^СЦЕНА\s+(\d+)", part)
        if m:
            num = int(m.group(1))
            scene_id = f"S{num:02d}"
            # Remove the header line itself, keep only the body
            lines = part.split("\n")
            header = lines[0].strip()
            body = "\n".join(lines[1:]).strip()
            scenes[scene_id] = body
    return scenes


def resolve_ingredient_path(raw_path: str) -> Path:
    """Resolve ingredient file path, handling legacy Cyrillic folder names."""
    for old_prefix, new_prefix in INGREDIENT_PATH_MAP.items():
        if raw_path.startswith(old_prefix):
            raw_path = new_prefix + raw_path[len(old_prefix):]
            break
    return BASE_DIR / raw_path


def format_clip_id(clip_id: str) -> str:
    """Convert clip ID like 'S03_A' to 'Сцена 3. Часть 1'."""
    parts = clip_id.split("_")
    scene_num = int(parts[0][1:])  # "S03" -> 3
    part_num = ord(parts[1]) - ord("A") + 1  # "A" -> 1, "B" -> 2
    return f"Сцена {scene_num}. Часть {part_num}"


def scene_badge(scene_id: str, scene_colors: dict) -> str:
    """Return HTML badge for a scene."""
    color = scene_colors.get(scene_id, "#888")
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
    meta = st.session_state["series_meta"]
    paths = st.session_state["series_paths"]
    scene_colors = meta["scene_colors"]
    scene_labels = meta["scene_labels"]
    char_display = meta["char_display"]
    frames_dir = paths["frames"]
    clips_dir = paths["clips"]

    clips = load_clips(str(paths["prompts"]))

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
        format_func=lambda x: char_display.get(x, x) if x != "Все" else "Все"
    )

    # Location filter
    all_locs = sorted(set(c["location"] for c in clips))
    selected_loc = st.sidebar.selectbox("Локация", ["Все"] + all_locs)

    # --- Apply filters ---
    filtered = clips
    if selected_scene != "Все":
        filtered = [c for c in filtered if c["scene_id"] == selected_scene]
    if selected_status != "Все":
        status_key = {"Готово": "done", "Частично": "partial", "Не начато": "todo"}[selected_status]
        filtered = [c for c in filtered if get_status(c["clip_id"], frames_dir, clips_dir) == status_key]
    if selected_char != "Все":
        filtered = [c for c in filtered if selected_char in c["characters"]]
    if selected_loc != "Все":
        filtered = [c for c in filtered if c["location"] == selected_loc]

    # --- Sidebar stats ---
    st.sidebar.markdown("---")
    all_statuses = [get_status(c["clip_id"], frames_dir, clips_dir) for c in clips]
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
        done_dur = sum(
            c.get("veo_duration", 0) for c, s in zip(clips, all_statuses) if s == "done"
        )
        st.markdown(f"""<div class="stat-card">
            <div class="number">{done_dur}с</div>
            <div class="label">Готовый хронометраж</div>
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
            color = scene_colors.get(current_scene, "#888")
            label = scene_labels.get(current_scene, current_scene)
            st.markdown(
                f'<h3 style="border-bottom:2px solid {color};padding-bottom:6px;'
                f'margin-top:24px;">{label}</h3>',
                unsafe_allow_html=True,
            )

        status = get_status(clip["clip_id"], frames_dir, clips_dir)
        status_label, status_icon = STATUS_MAP[status]
        status_class = f"status-{status}"

        # Expander per clip
        header_text = (
            f'{status_icon} {format_clip_id(clip["clip_id"])} — {clip["scene_description_ru"]}'
        )
        with st.expander(header_text, expanded=False):
            render_clip_card(clip, status, status_label, status_class)


def render_clip_card(clip: dict, status: str, status_label: str, status_class: str):
    """Render the full clip card inside an expander."""
    meta = st.session_state["series_meta"]
    paths = st.session_state["series_paths"]
    char_display = meta["char_display"]
    frames_dir = paths["frames"]
    clips_dir = paths["clips"]
    clip_id = clip["clip_id"]

    # --- Scenario text ---
    st.markdown("**Сценарий**")
    st.markdown(
        f'<div class="prompt-block">{clip["scene_description_ru"]}</div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")

    # --- Row 1: Status + Meta ---
    meta_col1, meta_col2, meta_col3, meta_col4 = st.columns([1, 1, 1, 1])
    with meta_col1:
        st.markdown(
            f'<span class="status-pill {status_class}">{status_label}</span>',
            unsafe_allow_html=True,
        )
    with meta_col2:
        chars_display = ", ".join(char_display.get(c, c) for c in clip["characters"])
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
            filepath = resolve_ingredient_path(ing["file"])
            with cols[i % len(cols)]:
                if filepath.exists():
                    st.image(str(filepath), width=120)
                    download_button_for_file(filepath, "Скачать", f"dl_ing_{clip_id}_{i}")
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
    st.markdown(f'<div class="prompt-label">VEO — Промпт A ({veo_info})</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="prompt-block">{clip["veo_prompt"]}</div>',
        unsafe_allow_html=True,
    )

    if clip.get("veo_prompt_b"):
        st.markdown(f'<div class="prompt-label">VEO — Промпт B ({veo_info})</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="prompt-block">{clip["veo_prompt_b"]}</div>',
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
    first_frame = frames_dir / f"{clip_id}_first.png"
    last_frame = frames_dir / f"{clip_id}_last.png"

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

    # --- Row 5: Video variants ---
    variants = get_video_variants(clip_id, clips_dir)
    total_variants = len(variants["prompt_a"]) + len(variants["prompt_b"])

    if total_variants > 0:
        st.markdown(f"**Видео — {total_variants} вариантов**")
        for group_key, group_label in [("prompt_a", "Промпт A"), ("prompt_b", "Промпт B")]:
            vids = variants[group_key]
            if not vids:
                continue
            st.markdown(f"*{group_label}* ({len(vids)} вариантов)")
            cols = st.columns(min(len(vids), 4))
            for i, vpath in enumerate(vids):
                with cols[i % len(cols)]:
                    st.video(str(vpath))
                    download_button_for_file(vpath, f"Скачать", f"dl_vid_{clip_id}_{group_key}_{i}")
    else:
        st.markdown("**Видео**")
        st.markdown(
            '<div style="background:#1A1D26;border:1px dashed #333;border-radius:8px;'
            'padding:40px;text-align:center;color:#555;">Видео — не сгенерировано</div>',
            unsafe_allow_html=True,
        )


def page_scenario():
    """Scenario page — full script text."""
    paths = st.session_state["series_paths"]
    scenario_file = paths["scenario"]

    st.header("Сценарий")

    if scenario_file.exists():
        text = scenario_file.read_text(encoding="utf-8")

        with st.expander("Полный сценарий", expanded=False):
            st.text(text)

        st.markdown("---")

        # Split by scene markers for per-scene navigation
        lines = text.split("\n")
        current_block = []
        blocks = []
        for line in lines:
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
        st.warning("Файл сценария не найден.")


def page_references():
    """Reference gallery — characters and locations."""
    meta = st.session_state["series_meta"]
    char_display = meta["char_display"]

    st.header("Референсы")

    tab_chars, tab_locs = st.tabs(["Персонажи", "Локации"])

    with tab_chars:
        st.subheader("Персонажи")
        if CHARS_DIR.exists():
            files = sorted(CHARS_DIR.glob("char_*"))
            if files:
                groups: dict[str, list[Path]] = {}
                for f in files:
                    parts = f.stem.split("_")
                    if len(parts) >= 2:
                        char_key = parts[1]
                        groups.setdefault(char_key, []).append(f)

                for char_key in sorted(groups):
                    display_name = char_display.get(
                        char_key.capitalize(), char_key.capitalize()
                    )
                    st.markdown(f"#### {display_name}")
                    char_files = groups[char_key]
                    cols = st.columns(4)
                    for i, fpath in enumerate(char_files):
                        with cols[i % 4]:
                            st.image(str(fpath), caption=fpath.name, width=200)
                            download_button_for_file(fpath, "Скачать", f"dl_ref_{fpath.stem}")
            else:
                st.info("Нет файлов персонажей.")
        else:
            st.warning("Папка персонажей не найдена.")

    with tab_locs:
        st.subheader("Локации")
        if LOCS_DIR.exists():
            files = sorted(LOCS_DIR.glob("loc_*"))
            if files:
                groups: dict[str, list[Path]] = {}
                for f in files:
                    parts = f.stem.split("_")
                    if len(parts) >= 2:
                        loc_key = parts[1]
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
                    cols = st.columns(4)
                    for i, fpath in enumerate(loc_files):
                        with cols[i % 4]:
                            st.image(str(fpath), caption=fpath.name, width=200)
                            download_button_for_file(fpath, "Скачать", f"dl_ref_{fpath.stem}")
            else:
                st.info("Нет файлов локаций.")
        else:
            st.warning("Папка локаций не найдена.")


def page_timeline():
    """Visual timeline of all clips."""
    meta = st.session_state["series_meta"]
    paths = st.session_state["series_paths"]
    scene_colors = meta["scene_colors"]
    scene_labels = meta["scene_labels"]
    char_display = meta["char_display"]
    frames_dir = paths["frames"]
    clips_dir = paths["clips"]

    st.header("Таймлайн")

    clips = load_clips(str(paths["prompts"]))
    current_scene = None

    for clip in clips:
        if clip["scene_id"] != current_scene:
            current_scene = clip["scene_id"]
            color = scene_colors.get(current_scene, "#888")
            label = scene_labels.get(current_scene, current_scene)
            st.markdown(
                f'<h4 style="color:{color};margin-top:20px;">{label}</h4>',
                unsafe_allow_html=True,
            )

        clip_id = clip["clip_id"]
        status = get_status(clip_id, frames_dir, clips_dir)
        _, status_icon = STATUS_MAP[status]
        dur = clip.get("veo_duration", 0)
        chars = ", ".join(char_display.get(c, c) for c in clip["characters"])

        # Timeline row
        cols = st.columns([1, 3, 1, 1])
        with cols[0]:
            st.markdown(f"**{status_icon} {format_clip_id(clip_id)}**")
        with cols[1]:
            st.markdown(clip["scene_description_ru"])
        with cols[2]:
            st.markdown(f"{chars}")
        with cols[3]:
            st.markdown(f"{dur}с")

        # Show video variants inline (no frame images in timeline)
        variants = get_video_variants(clip_id, clips_dir)
        all_vids = variants["prompt_a"] + variants["prompt_b"]

        if all_vids:
            st.caption(f"{len(all_vids)} вариантов видео")
            vid_cols = st.columns(min(len(all_vids), 4))
            for i, vpath in enumerate(all_vids):
                with vid_cols[i % len(vid_cols)]:
                    st.video(str(vpath))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    st.set_page_config(
        page_title="Путь Амина — Dashboard",
        page_icon="🧭",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    inject_css()

    # --- Discover series ---
    all_series = discover_series()
    if not all_series:
        st.error("Серии не найдены. Добавьте папку с meta.json в series/")
        return

    series_ids = list(all_series.keys())

    # --- Sidebar header ---
    st.sidebar.markdown(
        '<h1 style="text-align:center;color:#E8B849;">🧭 Путь Амина</h1>'
        '<p style="text-align:center;color:#888;font-size:0.85em;">'
        'Production Dashboard</p>',
        unsafe_allow_html=True,
    )

    # --- Series selector ---
    selected_id = st.sidebar.selectbox(
        "Серия",
        series_ids,
        format_func=lambda sid: f'{all_series[sid].get("icon", "")} {all_series[sid]["title"]}',
    )

    series_meta = all_series[selected_id]
    paths = series_paths(series_meta["_dir"])
    st.session_state["series_meta"] = series_meta
    st.session_state["series_paths"] = paths

    # --- Navigation ---
    page = st.sidebar.radio(
        "Навигация",
        ["Клипы", "Таймлайн", "Сценарий", "Референсы"],
        label_visibility="collapsed",
    )

    # --- Page routing ---
    if page == "Клипы":
        st.title(f'{series_meta.get("icon", "")} {series_meta["title"]} — Клипы')
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
        'Путь Амина<br>3D Pixar-style Animation<br>'
        'Nano Banana Pro + VEO 3.1</p>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
