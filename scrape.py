#!/usr/bin/env python3
import json
import sys
from pathlib import Path

def main() -> int:
    src_path = Path('products.json')
    dst_path = Path('catalog.json')

    if not src_path.exists():
        print('products.json not found', file=sys.stderr)
        dst_path.write_text('[]', encoding='utf-8')
        return 0

    try:
        products = json.loads(src_path.read_text(encoding='utf-8'))
    except Exception as exc:
        print(f'Failed to read products.json: {exc}', file=sys.stderr)
        return 1

    catalog = []
    for p in products or []:
        variants = p.get('variants') or []
        first_variant = variants[0] if variants else {}
        price_raw = first_variant.get('price')
        try:
            clearance_price = float(price_raw) if price_raw is not None else 0.0
        except Exception:
            clearance_price = 0.0

        images = p.get('images') or []
        image_urls = [img.get('src') for img in images if isinstance(img, dict) and img.get('src')]

        catalog.append({
            'id': p.get('id'),
            'name': p.get('title') or 'Untitled',
            'clearance_price': clearance_price,
            'image_urls': image_urls,
            'description': p.get('body_html') or ''
        })

    dst_path.write_text(json.dumps(catalog), encoding='utf-8')
    print(f'Wrote {len(catalog)} products to {dst_path}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())

