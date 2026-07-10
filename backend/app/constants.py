# Fixed categorical order — matches frontend/src/constants/categories.js.
# Colors are the dataviz skill's validated 8-hue categorical palette (light mode).
CATEGORY_COLORS = {
    "Food & Dining": "#2a78d6",
    "Groceries": "#1baf7a",
    "Transport & Vehicle": "#eda100",
    "Health & Medical": "#008300",
    "Entertainment": "#4a3aa7",
    "Shopping": "#e34948",
    "Utilities & Bills": "#e87ba4",
    "Other": "#eb6834",
}
DEFAULT_CATEGORY_COLOR = "#7b8496"  # app's --ink-light, for any uncategorized value
CATEGORIES = list(CATEGORY_COLORS.keys())

# Default essential/discretionary split used by the decision engine to soften
# "spend less" framing for categories like Health & Medical. Not user-editable
# in v1 — revisit if that turns out to matter.
ESSENTIAL_CATEGORIES = {"Groceries", "Health & Medical", "Utilities & Bills", "Transport & Vehicle"}
