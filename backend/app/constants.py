# Fixed categorical order — matches frontend/src/constants/categories.js.
# Colors are the dataviz skill's validated 8-hue categorical palette (light mode).
CATEGORY_COLORS = {
    "Eating Out": "#2a78d6",
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

# Trip's own category set — exactly the categories relevant to a trip, not the
# full main-app list. Kept separate from CATEGORIES/CATEGORY_COLORS so the main
# app's taxonomy and validated 8-hue palette are untouched. Only ever shown in
# trip-creation budgets and receipts tagged to a trip. Colors reuse the main
# palette's values for the 5 overlapping categories; Accommodation's violet was
# validated alongside them with the dataviz skill's palette checker (lightness,
# chroma, CVD separation all pass using the same direct-value-label convention
# every chart in this app already uses).
TRIP_CATEGORIES = ["Eating Out", "Transport & Vehicle", "Accommodation", "Entertainment", "Shopping", "Other"]
TRIP_CATEGORY_COLORS = {c: CATEGORY_COLORS[c] for c in TRIP_CATEGORIES if c in CATEGORY_COLORS}
TRIP_CATEGORY_COLORS["Accommodation"] = "#8a5fc9"
