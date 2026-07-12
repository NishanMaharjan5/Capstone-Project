import easyocr
import re
from typing import List, Dict, Any, Tuple
from app.ocr.preprocess import preprocess_receipt


class ReceiptExtractor:
    def __init__(self, languages=["en"]):
        self.reader = easyocr.Reader(languages, gpu=False)

    def preprocess_image(self, image_path: str):
        return preprocess_receipt(image_path)

    # ── OCR with bounding boxes ──
    def extract_text_with_boxes(self, image_path: str):
        processed = self.preprocess_image(image_path)
        results = self.reader.readtext(processed, detail=1, paragraph=False)
        print("\n=== RAW OCR ===")
        for bbox, text, conf in results:
            print(f"  '{text}' (conf: {conf:.2f})")
        return results

    # ── Group OCR chunks into rows by Y coordinate ──
    def group_into_rows(self, ocr_results, y_tolerance=12) -> List[List[Tuple]]:
        items = []
        for bbox, text, conf in ocr_results:
            if not text.strip():
                continue
            ys = [pt[1] for pt in bbox]
            xs = [pt[0] for pt in bbox]
            cy = sum(ys) / len(ys)
            cx = sum(xs) / len(xs)
            items.append((cy, cx, text.strip(), conf))

        items.sort(key=lambda x: x[0])

        rows = []
        current_row = []
        current_y = None

        for cy, cx, text, conf in items:
            if current_y is None or abs(cy - current_y) <= y_tolerance:
                current_row.append((cx, text, conf))
                current_y = cy if current_y is None else (current_y + cy) / 2
            else:
                if current_row:
                    current_row.sort(key=lambda x: x[0])
                    rows.append(current_row)
                current_row = [(cx, text, conf)]
                current_y = cy

        if current_row:
            current_row.sort(key=lambda x: x[0])
            rows.append(current_row)

        return rows

    def rows_to_lines(self, rows: List[List[Tuple]]) -> List[str]:
        lines = []
        for row in rows:
            line = " ".join(text for _, text, _ in row)
            lines.append(line)
        return lines

    def extract_text(self, image_path: str) -> List[str]:
        print("\n=== OCR DEBUG START ===")
        raw = self.extract_text_with_boxes(image_path)
        rows = self.group_into_rows(raw)
        lines = self.rows_to_lines(rows)
        print("\n=== RECONSTRUCTED ROWS ===")
        for i, line in enumerate(lines):
            print(f"  {i}: '{line}'")
        print(f"=== OCR END: {len(lines)} rows ===\n")
        return lines

    # ── Garbage line filter ──
    def _is_garbage_line(self, text: str) -> bool:
        text = text.strip()
        if not text:
            return True
        noise = sum(1 for c in text if c in '#@*&^%${}[]|\\~`?')
        if noise > 3:
            return True
        alnum = sum(1 for c in text if c.isalnum())
        if len(text) > 5 and alnum / len(text) < 0.4:
            return True
        return False

    # ── Sanity bound: a receipt total/line-item price is never absurdly large.
    # Prevents a mis-parsed phone number / order ID / invoice number from ever
    # being mistaken for a real amount, however it was produced. ──
    MAX_PLAUSIBLE_AMOUNT = 10_000_000

    def _is_plausible_amount(self, value: float) -> bool:
        return 0 < value <= self.MAX_PLAUSIBLE_AMOUNT

    # ── Normalize line for price extraction ──
    def _normalize_prices(self, text: str) -> str:
        # Collapse period-grouped thousands, e.g. "1.160.00" -> "1160.00",
        # "19.298.81" -> "19298.81" (some receipts use "." instead of "," to
        # group thousands, which otherwise reads as multiple decimal points).
        text = re.sub(
            r'\b\d{1,3}(?:\.\d{3})+\.\d{2}\b',
            lambda m: m.group().replace('.', '', m.group().count('.') - 1),
            text
        )
        text = re.sub(r'\b(\d+),(\d{2})\b', r'\1.\2', text)
        text = re.sub(r'(?<!\.)\b(\d+)\s(\d{2})\b', r'\1.\2', text)
        return text

    def _number_matches(self, text: str) -> List[re.Match]:
        fixed = self._normalize_prices(text)
        # Supports plain prices like 1491.09 and comma prices like 19,298.81.
        return list(re.finditer(r'(?<![\w.])(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d{1,2})?(?![\w.])', fixed))

    # ── Extract all prices from a line ──
    def _extract_all_prices(self, text: str) -> List[float]:
        prices = []
        for m in self._number_matches(text):
            try:
                v = float(m.group().replace(',', ''))
                if self._is_plausible_amount(v):
                    prices.append(v)
            except:
                pass
        return prices

    # ── Extract rightmost price from original line (before name cleaning) ──
    def _extract_rightmost_price(self, text: str) -> float | None:
        matches = self._number_matches(text)
        if not matches:
            return None
        try:
            v = float(matches[-1].group().replace(',', ''))
            return v if self._is_plausible_amount(v) else None
        except:
            return None

    def _is_numeric_only_line(self, text: str) -> bool:
        compact = re.sub(r'[\s\.,:;\-_/]+', '', text or '')
        return bool(compact) and compact.isdigit()

    def _has_letters(self, text: str) -> bool:
        return any(c.isalpha() for c in text or "")

    # ── Strict date validation ──
    def _is_valid_date(self, day: int, month: int, year: int) -> bool:
        if year < 2000 or year > 2099:
            return False
        if month < 1 or month > 12:
            return False
        if day < 1 or day > 31:
            return False
        if month in [4, 6, 9, 11] and day > 30:
            return False
        if month == 2 and day > 29:
            return False
        return True

    def _extract_date(self, lines: List[str]) -> str:
        joined = " ".join(lines[:25])
        joined = re.sub(r'(\d{4})-l(\d)', r'\1-1\2', joined)
        joined = re.sub(r'(\d{4})\.l(\d)', r'\1.1\2', joined)
        # Collapse a stray OCR period splitting a 4-digit year, e.g.
        # "202.6-07-03" -> "2026-07-03".
        joined = re.sub(r'\b(\d{3})\.(\d)(?=[\-\.])', r'\1\2', joined)

        months = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
                  "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}

        # Prefer visible Gregorian month-name dates before numeric Miti dates.
        for m in re.finditer(
            r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*[\s,]+(\d{1,2})[\s,]+(\d{4})\b',
            joined, re.IGNORECASE
        ):
            mo = months.get(m.group(1)[:3].lower(), 0)
            d, y = int(m.group(2)), int(m.group(3))
            if self._is_valid_date(d, mo, y):
                return f"{d:02d}/{mo:02d}/{y}"

        for m in re.finditer(
            r'\b(\d{1,2})[\s,]+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*[\s,]+(\d{4})\b',
            joined, re.IGNORECASE
        ):
            d = int(m.group(1))
            mo = months.get(m.group(2)[:3].lower(), 0)
            y = int(m.group(3))
            if self._is_valid_date(d, mo, y):
                return f"{d:02d}/{mo:02d}/{y}"

        for m in re.finditer(r'\b(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{4})\b', joined):
            d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if self._is_valid_date(d, mo, y):
                return f"{d:02d}/{mo:02d}/{y}"

        for m in re.finditer(r'\b(\d{4})[\/\-\.](\d{1,2})[\/\-\.](\d{1,2})\b', joined):
            y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if self._is_valid_date(d, mo, y):
                return f"{d:02d}/{mo:02d}/{y}"

        for m in re.finditer(
            r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*[\s,]+(\d{1,2})[\s,]+(\d{4})\b',
            joined, re.IGNORECASE
        ):
            mo = months.get(m.group(1)[:3].lower(), 0)
            d, y = int(m.group(2)), int(m.group(3))
            if self._is_valid_date(d, mo, y):
                return f"{d:02d}/{mo:02d}/{y}"

        for m in re.finditer(
            r'\b(\d{1,2})[\s,]+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*[\s,]+(\d{4})\b',
            joined, re.IGNORECASE
        ):
            d = int(m.group(1))
            mo = months.get(m.group(2)[:3].lower(), 0)
            y = int(m.group(3))
            if self._is_valid_date(d, mo, y):
                return f"{d:02d}/{mo:02d}/{y}"

        for m in re.finditer(
            r'(?:printed.?date|date)[:\s_]+(\d{4})[\-\.](\d{2})[\-\.](\d{2})',
            joined, re.IGNORECASE
        ):
            y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if self._is_valid_date(d, mo, y):
                return f"{d:02d}/{mo:02d}/{y}"

        return ""

    # ── Line classifiers ──
    def _is_total_line(self, text: str) -> bool:
        lower = text.lower()
        if "total amount inc vat" in lower or "total inc vat" in lower:
            return True
        if "grand total" in lower:
            return True
        if "total amount" in lower and "no. of items" not in lower and "taxable" not in lower:
            return True
        other = ["net total", "amount due", "balance due", "total due",
                 "invoice total", "total payable", "amount payable"]
        return any(k in lower for k in other)

    def _is_subtotal_line(self, text: str) -> bool:
        keywords = ["sub total", "subtotal", "sub-total", "net amount",
                    "taxable amount", "before tax"]
        lower = text.lower()
        return any(k in lower for k in keywords)

    def _is_tax_line(self, text: str) -> bool:
        lower = text.lower()
        return "tax amount" in lower and "taxable" not in lower

    # ── A line that IS the date/time header — must never be treated as a
    # price candidate. A bare year (e.g. "2026") or a misread time value
    # (OCR often turns "3:48 PM" into "3,48 PM") is a plausible-looking
    # number that can otherwise outrank the real total whenever a receipt
    # has no explicit "total" keyword line. ──
    def _is_date_line(self, text: str) -> bool:
        lower = text.lower()
        if re.search(r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{1,2}\b', lower):
            return True
        if re.search(r'\b\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4}\b', text):
            return True
        if re.search(r'\b\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2}\b', text):
            return True
        if re.search(r'\b\d{1,2}[:,]\d{2}\s*(am|pm)\b', lower):
            return True
        return False

    # ── A standalone currency-prefixed line ("Rs 1,535.00", "NPR 1,500")
    # is a strong, explicit total signal on minimalist receipts/order slips
    # that never say "total" at all — worth trusting ahead of the risky
    # "largest number on the receipt" last resort. ──
    def _is_currency_total_line(self, text: str) -> bool:
        return bool(re.match(r'^(rs\.?|npr\.?|nrs\.?)\s*[,:]?\s*\d', text.strip(), re.IGNORECASE))

    def _is_header_row(self, text: str) -> bool:
        keywords = ["item", "description", "qty", "quantity", "rate",
                    "amount", "total", "slno", "sl.no", "hs code",
                    "item code", "disc", "amountnrs", "basic rate", "ltem",
                    "tqtal", "t0tal"]
        lower = text.lower()
        matches = sum(1 for k in keywords if k in lower)
        return matches >= 2

    def _is_skip_line(self, text: str) -> bool:
        keywords = [
            "vat", "gst", "tax amount", "discount amount", "offer discount",
            "hs code", "item code", "page", "printed by", "print time",
            "printed date", "printed_date", "customer name", "customer address",
            "customer vat", "phone", "email", "www", "http", "invoice no",
            "bill no", "table:", "pax", "order by", "order id", "thank you",
            "please visit", "in words", "mode of payment", "transaction",
            "regd", "authorised signatory", "customer signatory", "remarks",
            "notes", "goods once", "chassis", "kms", "miti", "job card",
            "contact number", "e. & o.e", "e.&o.e", "no. of items",
            "amount in words", "invoice date", "total taxable", "taxable amount",
            "for biker", "sixty", "nepal rupees", "paise", "visit again",
            "estimate"
        ]
        lower = text.lower()
        return any(k in lower for k in keywords)

    # ── Vendor extraction ──
    def _extract_vendor(self, lines: List[str]) -> str:
        skip_starts = [
            "tax invoice", "abbreviated", "invoice", "receipt", "bill to",
            "ship to", "vat", "pan", "tel", "phone", "email", "www", "http",
            "customer", "date", "no.", "page", "bill no", "table", "pax",
            "hc ", "h.c", "order", "estimate", "print", "transaction",
            "invoice date", "miti", "job card", "regd", "mode of payment",
            "contact", "model", "chassis"
        ]
        business_keywords = [
            "pvt", "ltd", "depot", "store", "restaurant", "cafe", "bakery",
            "market", "shop", "center", "centre", "hotel", "pharmacy",
            "clinic", "hospital", "coffee", "foods", "traders", "enterprises",
            "suppliers", "services", "circle", "house", "kitchen"
        ]

        candidates = []
        for line in lines[:12]:
            clean = line.strip()
            if not clean or len(clean) < 3:
                continue
            if self._is_garbage_line(clean):
                continue
            lower = clean.lower()
            if any(lower.startswith(s) for s in skip_starts):
                continue
            if re.search(r'(invoice no|bill no|customer name|vat number|job card)', lower):
                continue
            if re.match(r'^[\d\s\.\,\:\-\/\(\)]+$', clean):
                continue
            letter_count = sum(c.isalpha() for c in clean)
            if letter_count < 3:
                continue
            candidates.append(clean)

        for i in range(len(candidates) - 1):
            combined = candidates[i] + " " + candidates[i + 1]
            if any(k in combined.lower() for k in ["pvt ltd", "pvt. ltd"]):
                combined = re.sub(r'\s*[_]\s*.*$', '', combined).strip()
                combined = re.sub(r'\s+(Mr|Mrs|Ms|Dr)\b.*$', '', combined).strip()
                combined = re.sub(r'(Pvt\.?\s*Ltd\.?).*$', r'\1', combined, flags=re.IGNORECASE).strip()
                return combined

        for c in candidates:
            if any(k in c.lower() for k in business_keywords):
                c = re.sub(r'\s*[_]\s*.*$', '', c).strip()
                c = re.sub(r'\s+(Mr|Mrs|Ms|_)\s*$', '', c).strip()
                return c

        return candidates[0] if candidates else "Unknown"

    # ── True numeric tokens, plus tokens that are almost certainly a numeric
    # column with one leading digit misread as a letter by OCR (e.g. "Z90.00"
    # from "290.00", "S0.00" from "50.00"). Only trips on tokens that already
    # look like "<1 letter><digits>.<2 digits>" so real name words survive. ──
    def _looks_like_numeric_token(self, token: str) -> bool:
        if re.fullmatch(r'[\d,]+(\.\d{1,2})?', token):
            return True
        return bool(re.fullmatch(r'[A-Za-z][\d,]{1,}\.\d{1,2}', token))

    # ── Item name cleaner — works on ORIGINAL line ──
    def _clean_item_name(self, text: str) -> str:
        cleaned = text.strip().replace('_', ' ')

        # Remove trailing numeric table columns: qty/rate/discount/amount.
        matches = self._number_matches(cleaned)
        if matches:
            cleaned = cleaned[:matches[-min(len(matches), 4)].start()].strip()

        # Catch a trailing price/qty column _number_matches missed because a
        # leading digit was OCR-misread as a letter.
        tokens = cleaned.split()
        while tokens and self._looks_like_numeric_token(tokens[-1]):
            tokens.pop()
        cleaned = " ".join(tokens)

        tokens = cleaned.split()
        # Remove leading SINo / HS Code numeric columns.
        while tokens and re.fullmatch(r'\d+', tokens[0]):
            tokens.pop(0)

        # Remove one leading item-code token, but keep real uppercase words like HEAD/LAMP.
        if tokens and re.search(r'\d', tokens[0]) and re.fullmatch(r'[A-Za-z0-9\-\/]+', tokens[0]):
            tokens.pop(0)

        cleaned = " ".join(tokens)
        cleaned = re.sub(r'[^\w\s\-\/]', '', cleaned).strip()
        cleaned = re.sub(r'^\d+\s*', '', cleaned).strip()
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()

        if not self._has_letters(cleaned):
            return ""

        return cleaned

    def _clean_item_fragment(self, text: str) -> str:
        cleaned = text.strip().replace('_', ' ')
        cleaned = re.sub(r'[^\w\s\-\/]', '', cleaned).strip()
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        if len(cleaned) < 2 or not self._has_letters(cleaned):
            return ""
        if cleaned.lower() in {"item", "items", "description", "particulars"}:
            return ""
        letters = sum(c.isalpha() for c in cleaned)
        digits = sum(c.isdigit() for c in cleaned)
        if digits and re.search(r'\b(tqtal|t0tal|total)\b', cleaned, re.IGNORECASE):
            return ""
        if digits > letters and re.search(r't[o0q]?tal', cleaned, re.IGNORECASE):
            return ""
        if self._is_skip_line(cleaned) or self._is_header_row(cleaned):
            return ""
        return cleaned

    def _fix_common_item_ocr(self, name: str) -> str:
        replacements = {
            r'\bBreaklast\b': 'Breakfast',
            r'\bmediuin\b': 'medium',
            r'\bFIONEY\b': 'HONEY',
            r'\bLalte\b': 'Latte',
            r'\blalte\b': 'Latte',
        }
        fixed = name
        for pattern, replacement in replacements.items():
            fixed = re.sub(pattern, replacement, fixed, flags=re.IGNORECASE)
        return fixed

    def _extract_quantity(self, line: str) -> float:
        fixed = self._normalize_prices(line)
        nums = []
        for match in re.finditer(r'\b\d+(?:\.\d{1,2})?\b', fixed):
            try:
                nums.append(float(match.group()))
            except:
                pass

        if len(nums) >= 4:
            quantity, unit_price, line_total = nums[-4], nums[-3], nums[-1]
            if 0 < quantity <= 999 and abs((quantity * unit_price) - line_total) <= max(1.0, line_total * 0.05):
                return quantity

        if len(nums) >= 3:
            quantity, unit_price, line_total = nums[-3], nums[-2], nums[-1]
            if 0 < quantity <= 999 and abs((quantity * unit_price) - line_total) <= max(1.0, line_total * 0.05):
                return quantity

        if len(nums) == 2:
            unit_price, line_total = nums
            if unit_price > 0:
                quantity = line_total / unit_price
                if 0 < quantity <= 999 and abs(quantity - round(quantity)) < 0.05:
                    return round(quantity)

        return 1

    def _extract_item_rows(self, lines: List[str], total: float) -> List[Dict]:
        items = []
        seen = set()
        header_found = False
        pending_fragments = []
        pending_price = None
        i = 0

        while i < len(lines):
            line = lines[i]

            if not header_found:
                if self._is_header_row(line):
                    header_found = True
                i += 1
                continue

            if self._is_total_line(line) or self._is_subtotal_line(line):
                break
            if self._is_skip_line(line) or self._is_garbage_line(line):
                i += 1
                continue

            prices = self._extract_all_prices(line)
            item_price = self._extract_rightmost_price(line)
            name_part = self._clean_item_name(line)

            if not prices:
                fragment = self._clean_item_fragment(line)
                if fragment and pending_price:
                    item_name = self._fix_common_item_ocr(fragment)
                    if item_name.lower() not in seen:
                        items.append({
                            "name": item_name,
                            "quantity": pending_price["quantity"],
                            "unit_price": pending_price["unit_price"],
                            "price": pending_price["price"]
                        })
                        seen.add(item_name.lower())
                        print(f"  ✅ Item: '{item_name}' x{pending_price['quantity']:g} → Rs.{pending_price['price']}")
                    pending_price = None
                    i += 1
                    continue
                if fragment:
                    pending_fragments.append(fragment)
                i += 1
                continue

            if item_price is None or item_price <= 0:
                i += 1
                continue
            if total > 0 and item_price >= total:
                i += 1
                continue

            quantity = self._extract_quantity(line)
            unit_price = item_price / quantity if quantity else item_price

            if not name_part and not pending_fragments:
                pending_price = {
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "price": item_price
                }
                i += 1
                continue

            next_fragment = ""
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                if (
                    not self._extract_all_prices(next_line)
                    and not self._is_skip_line(next_line)
                    and not self._is_total_line(next_line)
                    and not self._is_subtotal_line(next_line)
                ):
                    next_fragment = self._clean_item_fragment(next_line)

            name_parts = []
            if pending_fragments:
                name_parts.extend(pending_fragments)
                pending_fragments = []
            if name_part:
                name_parts.append(name_part)
            if next_fragment and (
                not name_part
                or name_part.endswith("-")
                or len(name_part.split()) <= 2
                or (next_fragment.isupper() and len(next_fragment.split()) <= 2)
            ):
                name_parts.append(next_fragment)
                i += 1

            item_name = " ".join(part.strip() for part in name_parts if part.strip()).strip()
            item_name = re.sub(r'-\s+', ' ', item_name)
            item_name = re.sub(r'\s+', ' ', item_name).strip(" -")
            item_name = self._fix_common_item_ocr(item_name)

            if len(item_name) < 3 or not self._has_letters(item_name):
                i += 1
                continue
            if item_name.lower() in seen:
                i += 1
                continue
            if self._is_skip_line(item_name):
                i += 1
                continue

            items.append({
                "name": item_name,
                "quantity": quantity,
                "unit_price": unit_price,
                "price": item_price
            })
            seen.add(item_name.lower())
            print(f"  ✅ Item: '{item_name}' x{quantity:g} → Rs.{item_price}")
            i += 1

        return items

    # ── Validation: try second-to-last price if sum doesn't match ──
    def _validate_and_fix_items(self, items: List[Dict], total: float, lines: List[str], tax_amount: float = 0.0) -> List[Dict]:
        if not items or total == 0:
            return items

        calc = sum(i["price"] for i in items)
        diff = abs(calc - total)

        if diff < total * 0.01:
            print(f"✅ Validation passed: sum={calc} matches total={total}")
            return items
        if tax_amount > 0 and abs((calc + tax_amount) - total) < max(1.0, total * 0.01):
            print(f"✅ Validation passed: sum={calc} + tax={tax_amount} matches total={total}")
            return items

        print(f"⚠️  Validation failed: sum={calc} != total={total}, diff={diff}")
        print("   Attempting re-extraction with second-to-last price...")

        new_items = []
        seen = set()
        header_found = False

        for i, line in enumerate(lines):
            if not header_found:
                if self._is_header_row(line):
                    header_found = True
                continue

            if self._is_skip_line(line) or self._is_garbage_line(line):
                continue
            if self._is_total_line(line) or self._is_subtotal_line(line):
                continue

            fixed = self._normalize_prices(line)
            matches = list(re.finditer(r'\b\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?\b', fixed))

            if len(matches) < 2:
                continue

            try:
                price_a = float(matches[-1].group().replace(',', ''))
                price_b = float(matches[-2].group().replace(',', ''))
            except:
                continue

            name_part = self._clean_item_name(line)
            if len(name_part) < 3 or name_part.lower() in seen:
                continue
            if self._is_skip_line(name_part):
                continue

            new_items.append({"name": name_part, "price": price_b, "_alt": price_a})
            seen.add(name_part.lower())

        if not new_items:
            return items

        calc_b = sum(i["price"] for i in new_items)
        calc_a = sum(i.get("_alt", 0) for i in new_items)

        print(f"   Alt sum (rightmost): {calc_a}, Alt sum (second): {calc_b}, Total: {total}")

        for item in new_items:
            item.pop("_alt", None)

        if abs(calc_b - total) < abs(calc - total):
            print(f"✅ Fixed: using second-to-last price, new sum={calc_b}")
            return new_items
        elif abs(calc_a - total) < abs(calc - total):
            for item, orig in zip(new_items, items):
                item["price"] = orig["price"]
            print(f"✅ Keeping original rightmost prices")
            return items
        else:
            print("   No improvement found, keeping original items")
            return items

    # ── Main extraction ──
    def extract_fields(self, lines: List[str]) -> Dict[str, Any]:
        print(f"\n=== extract_fields: {len(lines)} lines ===")
        for i, l in enumerate(lines):
            print(f"  {i}: '{l}'")

        data = {
            "vendor": "Unknown",
            "date": "",
            "items": [],
            "total": 0.0,
            "tax_amount": 0.0,
            "verified": False,
            "confidence": 0
        }

        clean_lines = [l for l in lines if not self._is_garbage_line(l)]

        # ── Vendor ──
        data["vendor"] = self._extract_vendor(clean_lines)
        print(f"✅ Vendor: {data['vendor']}")

        # ── Date ──
        data["date"] = self._extract_date(clean_lines)
        print(f"✅ Date: {data['date']}")

        # ── Total ──
        for line in clean_lines:
            if self._is_total_line(line):
                prices = self._extract_all_prices(line)
                if prices:
                    data["total"] = max(prices)
                    print(f"✅ Total (explicit): {data['total']}")
                    break

        if data["total"] == 0:
            for line in clean_lines:
                if self._is_subtotal_line(line):
                    prices = self._extract_all_prices(line)
                    if prices:
                        data["total"] = max(prices)
                        print(f"✅ Total (subtotal): {data['total']}")
                        break

        if data["total"] == 0:
            for line in clean_lines:
                if self._is_date_line(line):
                    continue
                if self._is_currency_total_line(line):
                    prices = self._extract_all_prices(line)
                    if prices:
                        data["total"] = max(prices)
                        print(f"✅ Total (currency-prefixed line): {data['total']}")
                        break

        if data["total"] == 0:
            all_prices = []
            for line in clean_lines:
                if not self._is_skip_line(line) and not self._is_garbage_line(line) and not self._is_date_line(line):
                    all_prices.extend(self._extract_all_prices(line))
            if all_prices:
                data["total"] = max(all_prices)
                print(f"✅ Total (largest): {data['total']}")

        for idx, line in enumerate(clean_lines):
            if self._is_tax_line(line):
                prices = self._extract_all_prices(line)
                if not prices and idx + 1 < len(clean_lines):
                    prices = self._extract_all_prices(clean_lines[idx + 1])
                if prices:
                    data["tax_amount"] = prices[-1]
                    print(f"✅ Tax amount: {data['tax_amount']}")
                    break

        # ── Items ──
        items = self._extract_item_rows(clean_lines, data["total"])

        # ── Validation safety net ──
        items = self._validate_and_fix_items(items, data["total"], clean_lines, data.get("tax_amount", 0.0))
        data["items"] = items

        # ── Confidence & verification ──
        if items and data["total"] > 0:
            calc = sum(i["price"] for i in items)
            diff = abs(calc - data["total"])
            tax_diff = abs((calc + data.get("tax_amount", 0)) - data["total"])
            if diff < 1.0:
                data["verified"] = True
                data["confidence"] = 100
            elif data.get("tax_amount", 0) > 0 and tax_diff < 1.0:
                data["verified"] = True
                data["confidence"] = 100
            elif diff < data["total"] * 0.05:
                data["verified"] = True
                data["confidence"] = 85
            elif diff < data["total"] * 0.15:
                data["confidence"] = 60
            else:
                data["confidence"] = 30
        elif data["total"] > 0:
            data["confidence"] = 40

        print(f"\n=== RESULT ===")
        print(f"Vendor: {data['vendor']} | Date: {data['date']} | Total: {data['total']}")
        print(f"Items: {len(data['items'])} | Verified: {data['verified']} | Confidence: {data['confidence']}%")
        return data


receipt_extractor = ReceiptExtractor()
print("=== EXTRACTOR.PY LOADED SUCCESSFULLY ===")
