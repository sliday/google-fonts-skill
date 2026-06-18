# Broken Google Fonts Embed URLs (css2 endpoint uses commas instead of semicolons)

## Description

The `generate_embed` function in `src/google_fonts_mcp/core.py` generates broken Google Fonts embed URLs. It uses the `css2` endpoint but constructs weight values with **commas** (the old `css` API syntax) instead of **semicolons** (the current `css2` API syntax). These malformed URLs return HTTP 400.

Google Fonts has two API endpoints:

- **css** (old): `https://fonts.googleapis.com/css?family=Roboto:400,700` — comma-separated weights
- **css2** (current): `https://fonts.googleapis.com/css2?family=Roboto:wght@400;700` — semicolon-separated weights

## Reproduction Steps

1. Clone the repository
2. Run:
   ```bash
   python3 -c "
   import sys; sys.path.insert(0,'src')
   from core import generate_embed
   print(generate_embed('Roboto', '', '300,400,700', ''))
   "
   ```
3. Observe the output URL uses `wght@300,400,700` (commas)
4. Test the generated URL:
   ```bash
   curl -sI "https://fonts.googleapis.com/css2?family=Roboto:wght@300,400,700&display=swap" | head -3
   ```
5. Observe **HTTP/2 400** response

## Expected Behavior

The generated URL should use `wght@300;400;700` (semicolons) and return **HTTP/2 200**.

## Actual Behavior

The generated URL uses `wght@300,400,700` (commas) and returns **HTTP/2 400**.

## Root Cause

In `src/google_fonts_mcp/core.py` lines 295 and 297, weight values are interpolated directly into the URL without replacing commas with semicolons:

```python
# Line 295
families.append(f"family={encode_font(heading)}:wght@{heading_weights}")
# Line 297
families.append(f"family={encode_font(body)}:wght@{body_weights}")
```

## Fix Applied

Replaced commas with semicolons in the weight values before URL construction:

```python
families.append(f"family={encode_font(heading)}:wght@{heading_weights.replace(',', ';')}")
families.append(f"family={encode_font(body)}:wght@{body_weights.replace(',', ';')}")
```

## Test Commands

After fix, verify with:

```bash
# Python verification
python3 -c "
import sys; sys.path.insert(0,'src')
from core import generate_embed
url = generate_embed('Roboto', '', '300,400,700', '')
print(url)
assert 'wght@300;400;700' in url, f'Expected semicolons in URL, got: {url}'
print('OK - URL contains semicolons')
"

# Curl verification
curl -sI "https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap" | head -3
# Should return: HTTP/2 200
```
