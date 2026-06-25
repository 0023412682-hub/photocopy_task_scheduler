import os

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:  # pragma: no cover
    Image = None
    ImageTk = None
    PIL_AVAILABLE = False

DEFAULT_ALIASES = {
    "add": ["Add", "Import_task"],
    "create": ["Add", "Import_task"],
    "new": ["Add", "Import_task"],
    "update": ["Update", "Edit", "Save"],
    "edit": ["Edit", "Update"],
    "save": ["Save", "Save_task", "Save CSV"],
    "delete": ["Delete", "Delete_task"],
    "remove": ["Delete", "Delete_task"],
    "reset": ["Reset", "Refresh"],
    "refresh": ["Refresh", "Reset"],
    "filter": ["Filter", "Search"],
    "search": ["Search", "Filter"],
    "import": ["Import", "Import_task", "Info_data"],
    "load": ["Import", "Import_task", "Info_data"],
    "data": ["Info_data", "Task_List", "Import_task"],
    "report": ["Report", "H_Report", "Export_Report"],
    "export": ["Export PDF", "Export_Report", "Save CSV"],
    "simulation": ["Simulation", "Simulation_Setup", "Run", "Run_Simulation"],
    "simulation_setup": ["Simulation_Setup", "Simulation", "Processing"],
    "run": ["Run", "Simulation", "Play_Simulation", "Run_Simulation"],
    "run_simulation": ["Run_Simulation", "Run", "Play_Simulation", "Simulation"],
    "play": ["Simulation", "Play_Simulation", "Run"],
    "pause": ["Pause"],
    "overview": ["Overview", "Information", "System_Info", "Comparison_Algorithm"],
    "fast": ["Fast", "Run", "Simulation"],
    "process": ["Process", "Process_result", "Processing", "Simulation"],
    "info": ["Information", "Info_data", "System_Info"],
    "info_data": ["Info_data", "Task_List", "Import_task"],
    "fcfs": ["FCFS", "Best_Algorithm"],
    "sjf": ["SJF", "Shortest"],
    "priority": ["Priority"],
    "round_robin": ["Round_Robin", "Refresh"],
    "b_printer": ["B_Printer", "B-Printer", "Printer", "Photocopier"],
    "g_printer": ["G_Printer", "G-Printer", "Printer", "Photocopier"],
    "r_printer": ["R_Printer", "R-Printer", "Printer", "Photocopier"],
    "p_printer": ["Printer", "Photocopier"],
}

PREFIXES = ("",)
EXTENSIONS = (".png", ".jpg", ".jpeg")


def normalize_icon_name(value):
    text = str(value or "").lower().strip()
    for char in (" ", "-", "."):
        text = text.replace(char, "_")
    while "__" in text:
        text = text.replace("__", "_")
    return text


def _add_candidate(candidates, name):
    if not name:
        return
    raw = str(name).strip()
    if raw and raw not in candidates:
        candidates.append(raw)


def build_candidates(filename, aliases=None):
    raw = str(filename or "").strip()
    base, ext = os.path.splitext(raw)
    base = base or raw
    candidates = []

    if ext:
        _add_candidate(candidates, raw)
    else:
        for extension in EXTENSIONS:
            _add_candidate(candidates, raw + extension)

    variants = {
        base,
        base.replace("_", " "),
        base.replace(" ", "_"),
        base.replace("-", "_"),
        base.replace("_", "-"),
    }
    for variant in variants:
        for prefix in PREFIXES:
            for extension in EXTENSIONS:
                _add_candidate(candidates, prefix + variant + extension)

    alias_map = dict(DEFAULT_ALIASES)
    if aliases:
        alias_map.update(aliases)

    normalized_base = normalize_icon_name(base)
    for group, names in alias_map.items():
        normalized_group = normalize_icon_name(group)
        if normalized_base == normalized_group or normalized_group in normalized_base or normalized_base in normalized_group:
            for alias_name in names:
                alias_base, alias_ext = os.path.splitext(str(alias_name))
                if alias_ext:
                    _add_candidate(candidates, alias_name)
                else:
                    for extension in EXTENSIONS:
                        _add_candidate(candidates, str(alias_name) + extension)
    return candidates, base


def resolve_icon_path(icon_dir, filename, aliases=None):
    if not filename:
        return None
    if os.path.isabs(str(filename)) and os.path.exists(str(filename)):
        return str(filename)

    candidates, base = build_candidates(filename, aliases=aliases)
    for name in candidates:
        path = os.path.join(icon_dir, name)
        if os.path.exists(path):
            return path

    wanted = normalize_icon_name(base)
    try:
        for name in os.listdir(icon_dir):
            stem, ext = os.path.splitext(name)
            if ext.lower() not in EXTENSIONS:
                continue
            normalized = normalize_icon_name(stem)
            if normalized == wanted or wanted in normalized or normalized in wanted:
                return os.path.join(icon_dir, name)
    except Exception:
        pass

    return None


def load_icon(owner, icon_dir, filename, size=(40, 40), *, aliases=None, crop_transparency=True, keep_aspect=True):
    """Load PNG/JPG thành PhotoImage kích thước cố định và giữ reference trên owner."""
    path = resolve_icon_path(icon_dir, filename, aliases=aliases)
    if not path or not PIL_AVAILABLE:
        return None
    try:
        image = Image.open(path).convert("RGBA")
        if crop_transparency:
            alpha = image.getchannel("A")
            bbox = alpha.getbbox()
            if bbox:
                image = image.crop(bbox)
        try:
            resample_filter = Image.Resampling.LANCZOS
        except AttributeError:  # pragma: no cover
            resample_filter = Image.LANCZOS

        if keep_aspect:
            image.thumbnail(size, resample_filter)
            canvas = Image.new("RGBA", size, (255, 255, 255, 0))
            x = (size[0] - image.width) // 2
            y = (size[1] - image.height) // 2
            canvas.paste(image, (x, y), image)
        else:
            canvas = image.resize(size, resample_filter)

        photo = ImageTk.PhotoImage(canvas)
        if not hasattr(owner, "images") or getattr(owner, "images") is None:
            owner.images = {}
        key = f"{filename}_{size}_{len(owner.images)}"
        owner.images[key] = photo
        if not hasattr(owner, "image_refs") or getattr(owner, "image_refs") is None:
            owner.image_refs = []
        owner.image_refs.append(photo)
        return photo
    except Exception:
        return None
