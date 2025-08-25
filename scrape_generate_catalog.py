# -*- coding: utf-8 -*-
# Colab-ready script: scrape + generate HTML catalog with First/Last/Go-to pagination,
# cart persistence, image/description modal, and "Email Inquiry" that adds to cart
# and emails the entire cart with clean formatting.


import requests
import json
import re
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor


# -----------------------------
# Scrape products
# -----------------------------
all_products = []
page = 1


def clean_description(text: str) -> str:
    """Remove any sentence mentioning 'France and Son' or 'France & Son' (case-insensitive)."""
    if not text:
        return ""
    # Normalize whitespace
    normalized = re.sub(r"\s+", " ", text).strip()
    # Split into sentences and filter
    sentences = re.split(r"(?<=[.!?])\s+", normalized)
    filtered = [s for s in sentences if not re.search(r"\bfrance\s*(?:&|and)\s*son\b", s, flags=re.IGNORECASE)]
    cleaned = " ".join(filtered).strip()
    return cleaned


def fetch_description(handle):
    url = f"https://franceandson.com/products/{handle}"
    try:
        res = requests.get(url, timeout=20)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            json_tag = soup.find("script", type="application/ld+json")
            if json_tag and json_tag.string:
                try:
                    data = json.loads(json_tag.string)
                    if isinstance(data, list):
                        # Some pages embed a list of ld+json objects
                        for obj in data:
                            if isinstance(obj, dict) and "description" in obj:
                                desc = obj.get("description", "")
                                return clean_description((desc or "").strip())
                    else:
                        desc = data.get("description", "")
                        return clean_description((desc or "").strip())
                except Exception:
                    # Non-JSON or multiple script tags; ignore
                    pass
    except Exception:
        return ""
    return ""


while True:
    url = f"https://franceandson.com/collections/clearance/products.json?page={page}"
    res = requests.get(url, timeout=20)
    if res.status_code != 200:
        break


    data = res.json()
    products = data.get("products", [])
    if not products:
        break


    handles = [p.get("handle", "") for p in products]


    # Fetch descriptions in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        descriptions = list(executor.map(fetch_description, handles))


    for i, p in enumerate(products):
        variant = p["variants"][0] if p.get("variants") else {}
        # Prefer discounted/current price over compare_at_price (original price)
        retail_price = variant.get("price") or variant.get("compare_at_price")
        try:
            retail_price = float(retail_price) if retail_price else 0.0
        except Exception:
            retail_price = 0.0


        images = p.get("images", [])
        image_urls = [img.get("src", "") for img in images if img.get("src")]


        all_products.append({
            "id": p.get("id"),
            "name": p.get("title", "Untitled"),
            "retail_price": retail_price,
            "image_urls": image_urls,
            "description": descriptions[i] if i < len(descriptions) else ""
        })
    page += 1


# -----------------------------
# Pagination settings
# -----------------------------
PRODUCTS_PER_PAGE = 20  # 4 columns x 5 rows


# -----------------------------
# Generate HTML gallery
# -----------------------------
html_file = "Capital_Restoration_Catalog.html"


html_str = f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Capital Restoration Catalog</title>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600&family=Inter:wght@300;400;500&display=swap" rel="stylesheet">
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
    font-family: 'Inter', sans-serif;
    margin: 0;
    background: #f8f7f4;
    line-height: 1.6;
    color: #2b2b2b;
}}
.container {{
    max-width: 1600px;
    margin: 0 auto;
    padding: 30px;
}}
.header {{
    text-align: center;
    margin-bottom: 40px;
    padding: 40px 0;
    background: linear-gradient(135deg, #3a3a3a 0%, #2b2b2b 100%);
    color: #e8e6e1;
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.1);
}}
.header h1 {{
    font-size: 3em;
    margin-bottom: 15px;
    font-weight: 300;
    letter-spacing: 1px;
    font-family: 'Playfair Display', serif;
}}
.header p {{
    font-size: 1.2em;
    opacity: 0.9;
    font-weight: 300;
    margin-bottom: 20px;
}}
.retail-notice {{
    background: #8b7d6b;
    color: #f8f7f4;
    padding: 12px 25px;
    border-radius: 25px;
    font-size: 16px;
    font-weight: 400;
    display: inline-block;
    letter-spacing: 0.5px;
}}


.gallery-container {{
    display: flex;
    flex-direction: column;
    align-items: center;
}}


.search-bar {{
    width: 100%;
    max-width: 600px;
    padding: 18px 25px;
    font-size: 18px;
    border: 2px solid #d1c7b7;
    border-radius: 30px;
    margin-bottom: 40px;
    outline: none;
    transition: all 0.3s ease;
    background: #fff;
    color: #2b2b2b;
    font-family: 'Inter', sans-serif;
}}
.search-bar:focus {{
    border-color: #8b7d6b;
    box-shadow: 0 0 0 3px rgba(139, 125, 107, 0.1);
}}
.search-bar::placeholder {{
    color: #a59e94;
}}


.gallery {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 30px;
    width: 100%;
    margin-bottom: 40px;
}}


.product-card {{
    background: #fff;
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 6px 25px rgba(0,0,0,0.08);
    cursor: pointer;
    transition: all 0.4s ease;
    display: flex;
    flex-direction: column;
    height: 420px;
    border: 1px solid #e8e6e1;
    position: relative;
}}
.product-card:hover {{
    transform: translateY(-8px);
    box-shadow: 0 20px 40px rgba(0,0,0,0.15);
    border-color: #c8b8a9;
}}
.product-card img {{
    width: 100%;
    height: 240px;
    object-fit: cover;
    transition: transform 0.5s ease;
}}
.product-card:hover img {{
    transform: scale(1.05);
}}
.product-info {{
    padding: 20px;
    text-align: center;
    flex-grow: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
    background: #faf9f7;
    transition: all 0.4s ease;
}}
.product-card:hover .product-info {{
    background: #f3f1ec;
}}
.product-name {{
    font-weight: 500;
    font-size: 17px;
    margin-bottom: 12px;
    color: #2b2b2b;
    line-height: 1.4;
    font-family: 'Playfair Display', serif;
}}
.product-price {{
    font-size: 20px;
    color: #b29764;
    font-weight: 600;
    margin-bottom: 8px;
}}
.product-retail-note {{
    font-size: 13px;
    color: #a59e94;
    font-style: italic;
    letter-spacing: 0.3px;
}}
.add-to-cart-btn {{
    position: absolute;
    top: 15px;
    right: 15px;
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.9);
    border: 1px solid #e8e6e1;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.3s ease;
    opacity: 0;
    transform: translateY(10px);
    z-index: 10;
}}
.product-card:hover .add-to-cart-btn {{
    opacity: 1;
    transform: translateY(0);
}}
.add-to-cart-btn:hover {{
    background: #b29764;
    color: white;
    border-color: #b29764;
}}
.add-to-cart-btn.added {{
    background: #b29764;
    color: white;
    border-color: #b29764;
}}


.cart-indicator {{
    position: fixed;
    top: 20px;
    right: 20px;
    background: #b29764;
    color: white;
    width: 50px;
    height: 50px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    font-size: 18px;
    cursor: pointer;
    box-shadow: 0 4px 15px rgba(178, 151, 100, 0.3);
    z-index: 100;
    transition: all 0.3s ease;
}}
.cart-indicator:hover {{
    transform: scale(1.05);
    box-shadow: 0 6px 20px rgba(178, 151, 100, 0.4);
}}


/* Modal Styles */
.modal {{
    display: none;
    position: fixed;
    z-index: 10000;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    overflow: auto;
    background-color: rgba(43, 43, 43, 0.95);
    align-items: center;
    justify-content: center;
    padding: 20px;
    opacity: 0;
    transition: opacity 0.3s ease;
}}
.modal.show {{
    display: flex;
    opacity: 1;
}}
.modal-content {{
    background: #faf9f7;
    max-width: 1400px;
    width: 95%;
    max-height: 95vh;
    position: relative;
    display: flex;
    flex-wrap: wrap;
    gap: 40px;
    border-radius: 20px;
    overflow: hidden;
    margin: auto;
    box-shadow: 0 30px 60px rgba(0,0,0,0.3);
    border: 1px solid #d1c7b7;
    transform: scale(0.95);
    transition: transform 0.3s ease;
}}
.modal.show .modal-content {{
    transform: scale(1);
}}
.close {{
    position: absolute;
    top: 20px;
    right: 30px;
    font-size: 40px;
    font-weight: 300;
    color: #2b2b2b;
    cursor: pointer;
    z-index: 1001;
    background: rgba(250, 249, 247, 0.9);
    width: 50px;
    height: 50px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    line-height: 1;
    transition: all 0.3s ease;
    border: 1px solid #d1c7b7;
}}
.close:hover {{
    background: #e8e6e1;
    transform: rotate(90deg);
}}


.left-column {{
    flex: 1.2;
    min-width: 500px;
    display: flex;
    flex-direction: column;
    align-items: center;
    position: relative;
    padding: 50px 40px 40px 50px;
    background: #fff;
}}
.slideshow-container {{
    position: relative;
    width: 100%;
    max-width: 600px;
}}
.slideshow {{
    width: 100%;
    position: relative;
}}
.slideshow img {{
    width: 100%;
    max-height: 500px;
    object-fit: contain;
    border-radius: 12px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    opacity: 0;
    position: absolute;
    top: 0;
    left: 0;
    transition: opacity 0.5s ease;
}}
.slideshow img.active {{
    opacity: 1;
    position: relative;
}}
.slide-info {{
    font-size: 16px;
    text-align: center;
    margin-top: 20px;
    color: #8b7d6b;
    font-style: italic;
}}
.image-nav {{
    position: absolute;
    top: 50%;
    transform: translateY(-50%);
    width: 100%;
    display: flex;
    justify-content: space-between;
    padding: 0 15px;
    pointer-events: none;
}}
.image-nav button {{
    pointer-events: auto;
    width: 55px;
    height: 55px;
    background-color: rgba(43, 43, 43, 0.8);
    color: #faf9f7;
    border: 1px solid #8b7d6b;
    border-radius: 50%;
    font-size: 22px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.3s ease;
    font-weight: 300;
}}
.image-nav button:hover {{
    background-color: #2b2b2b;
    transform: scale(1.1);
}}


.right-column {{
    flex: 0.8;
    min-width: 350px;
    padding: 50px 40px 40px 20px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}}
.right-column h2 {{
    margin-top: 0;
    font-size: 32px;
    color: #2b2b2b;
    margin-bottom: 15px;
    font-weight: 400;
    line-height: 1.3;
    font-family: 'Playfair Display', serif;
}}
.modal-price {{
    font-size: 28px;
    color: #b29764;
    font-weight: 600;
    margin-bottom: 8px;
}}
.modal-retail-note {{
    font-size: 15px;
    color: #a59e94;
    margin-bottom: 15px;
    font-style: italic;
    letter-spacing: 0.5px;
}}
.modal-add-to-cart {{
    display: inline-block;
    padding: 12px 25px;
    background: #b29764;
    color: white;
    border: none;
    border-radius: 25px;
    cursor: pointer;
    font-weight: 500;
    font-size: 16px;
    transition: all 0.3s ease;
    margin-bottom: 10px;
    text-align: center;
}}
.modal-add-to-cart:hover {{
    background: #9c8357;
    transform: translateY(-2px);
}}
.modal-add-to-cart.added {{
    background: #8b7d6b;
}}
.contact-btn {{
    display: inline-block;
    margin: 10px 0;
    padding: 14px 28px;
    background: #8b7d6b;
    color: #faf9f7;
    text-decoration: none;
    border-radius: 30px;
    text-align: center;
    transition: all 0.3s ease;
    font-weight: 500;
    font-size: 16px;
    border: 2px solid #8b7d6b;
    letter-spacing: 0.5px;
}}
.contact-btn:hover {{
    background: #7a6d5c;
    border-color: #7a6d5c;
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(139, 125, 107, 0.3);
}}
.description {{
    font-size: 17px;
    line-height: 1.7;
    color: #555;
    margin-top: 20px;
    max-height: 250px;
    overflow-y: auto;
    padding-right: 15px;
    font-weight: 300;
}}
.description::-webkit-scrollbar {{
    width: 6px;
}}
.description::-webkit-scrollbar-track {{
    background: #e8e6e1;
    border-radius: 3px;
}}
.description::-webkit-scrollbar-thumb {{
    background: #8b7d6b;
    border-radius: 3px;
}}


/* Pagination (First/Prev/Numbers/Next/Last + Go to Page) */
.pagination-container {{
    display: flex;
    justify-content: center;
    align-items: center;
    margin: 40px 0;
    gap: 15px;
    flex-wrap: wrap;
}}
.pagination-controls {{
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
}}
.pagination-btn {{
    padding: 12px 20px;
    background: #3a3a3a;
    color: #faf9f7;
    border: 2px solid #3a3a3a;
    border-radius: 10px;
    cursor: pointer;
    font-weight: 500;
    font-size: 15px;
    transition: all 0.3s ease;
    min-width: 90px;
    text-align: center;
}}
.pagination-btn:hover:not(:disabled) {{
    background: #2b2b2b;
    border-color: #2b2b2b;
    transform: translateY(-2px);
}}
.pagination-btn:disabled {{
    opacity: 0.5;
    cursor: not-allowed;
}}
.pagination-numbers {{
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}}
.page-btn {{
    padding: 10px 14px;
    cursor: pointer;
    border: 2px solid #d1c7b7;
    background: #faf9f7;
    border-radius: 8px;
    font-weight: 500;
    font-size: 15px;
    transition: all 0.3s ease;
    min-width: 42px;
    color: #2b2b2b;
}}
.page-btn.active {{
    background: #8b7d6b;
    color: #faf9f7;
    border-color: #8b7d6b;
}}
.page-btn:hover:not(.active) {{
    background: #e8e6e1;
    border-color: #8b7d6b;
    transform: translateY(-1px);
}}


.goto-wrapper {{
    display: flex;
    gap: 8px;
    align-items: center;
}}
.goto-input {{
    width: 90px;
    padding: 10px 12px;
    border-radius: 8px;
    border: 2px solid #d1c7b7;
    background: #fff;
    font-size: 15px;
}}
.goto-button {{
    padding: 10px 14px;
    border-radius: 8px;
    border: 2px solid #3a3a3a;
    background: #3a3a3a;
    color: #faf9f7;
    cursor: pointer;
    font-size: 15px;
}}
.goto-button:hover {{
    background: #2b2b2b;
    border-color: #2b2b2b;
}}


/* Cart Modal */
.cart-modal {{
    display: none;
    position: fixed;
    z-index: 10000;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(43, 43, 43, 0.95);
    align-items: center;
    justify-content: center;
    padding: 20px;
    opacity: 0;
    transition: opacity 0.3s ease;
}}
.cart-modal.show {{
    display: flex;
    opacity: 1;
}}
.cart-content {{
    background: #faf9f7;
    width: 90%;
    max-width: 800px;
    max-height: 90vh;
    border-radius: 20px;
    padding: 40px;
    overflow-y: auto;
    box-shadow: 0 30px 60px rgba(0,0,0,0.3);
    transform: scale(0.95);
    transition: transform 0.3s ease;
}}
.cart-modal.show .cart-content {{
    transform: scale(1);
}}
.cart-title {{
    font-size: 28px;
    margin-bottom: 25px;
    color: #2b2b2b;
    font-family: 'Playfair Display', serif;
    text-align: center;
}}
.cart-items {{
    margin-bottom: 30px;
}}
.cart-item {{
    display: flex;
    align-items: center;
    padding: 15px 0;
    border-bottom: 1px solid #e8e6e1;
}}
.cart-item-img {{
    width: 80px;
    height: 80px;
    object-fit: cover;
    border-radius: 8px;
    margin-right: 20px;
}}
.cart-item-details {{
    flex-grow: 1;
}}
.cart-item-name {{
    font-weight: 500;
    margin-bottom: 5px;
    font-family: 'Playfair Display', serif;
}}
.cart-item-price {{
    color: #b29764;
    font-weight: 600;
}}
.remove-from-cart {{
    background: none;
    border: none;
    color: #e74c3c;
    cursor: pointer;
    font-size: 20px;
    padding: 5px;
    margin-left: 15px;
}}
.cart-total {{
    font-size: 22px;
    font-weight: 600;
    text-align: right;
    margin: 20px 0;
    padding-top: 20px;
    border-top: 2px solid #e8e6e1;
}}
.cart-total span {{
    color: #b29764;
}}
.cart-actions {{
    display: flex;
    justify-content: space-between;
    gap: 15px;
}}
.cart-btn {{
    padding: 15px 25px;
    border-radius: 30px;
    font-weight: 500;
    font-size: 16px;
    cursor: pointer;
    transition: all 0.3s ease;
    flex: 1;
    text-align: center;
}}
.continue-shopping {{
    background: #e8e6e1;
    color: #2b2b2b;
    border: 2px solid #e8e6e1;
}}
.continue-shopping:hover {{
    background: #d1c7b7;
    border-color: #d1c7b7;
}}
.email-inquiry {{
    background: #b29764;
    color: white;
    border: 2px solid #b29764;
    text-decoration: none;
}}
.email-inquiry:hover {{
    background: #9c8357;
    border-color: #9c8357;
}}


.empty-cart {{
    text-align: center;
    padding: 40px 0;
    color: #a59e94;
    font-style: italic;
}}


footer {{
    margin-top: 60px;
    background: linear-gradient(135deg, #3a3a3a 0%, #2b2b2b 100%);
    color: #e8e6e1;
    padding: 50px;
    text-align: center;
    font-size: 18px;
    border-radius: 16px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.1);
}}
footer a {{
    color: #c8b8a9;
    text-decoration: none;
    transition: color 0.3s ease;
}}
footer a:hover {{
    color: #faf9f7;
    text-decoration: underline;
}}
.footer-title {{
    font-size: 32px;
    font-weight: 300;
    margin-bottom: 20px;
    letter-spacing: 1px;
}}
.footer-divider {{
    border: 1px solid #555;
    margin: 25px auto;
    max-width: 250px;
    opacity: 0.6;
}}
.footer-note {{
    font-style: italic;
    opacity: 0.8;
    margin-top: 20px;
    font-size: 16px;
}}


/* Scroll to top button */
.scroll-to-top {{
    position: fixed;
    bottom: 30px;
    right: 30px;
    width: 50px;
    height: 50px;
    border-radius: 50%;
    background: #b29764;
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    opacity: 0;
    visibility: hidden;
    transition: all 0.3s ease;
    z-index: 99;
}}
.scroll-to-top.visible {{
    opacity: 1;
    visibility: visible;
}}
.scroll-to-top:hover {{
    background: #9c8357;
    transform: translateY(-3px);
}}


/* Responsive */
@media (max-width: 1400px) {{
    .gallery {{
        grid-template-columns: repeat(3, 1fr);
    }}
    .modal-content {{
        max-width: 1200px;
    }}
}}
@media (max-width: 1100px) {{
    .gallery {{
        grid-template-columns: repeat(2, 1fr);
    }}
    .left-column, .right-column {{
        min-width: 100%;
        padding: 30px;
    }}
    .left-column {{
        padding-bottom: 20px;
    }}
    .slideshow img {{
        max-height: 400px;
    }}
    .modal-content {{
        flex-direction: column;
        max-height: 90vh;
        gap: 20px;
    }}
    .cart-actions {{
        flex-direction: column;
    }}
}}
@media (max-width: 768px) {{
    .container {{
        padding: 20px;
    }}
    .gallery {{
        grid-template-columns: 1fr;
        gap: 25px;
    }}
    .header h1 {{
        font-size: 2.2em;
    }}
    .pagination-container {{
        flex-direction: column;
        gap: 20px;
    }}
    .pagination-numbers {{
        order: -1;
    }}
    .image-nav button {{
        width: 45px;
        height: 45px;
        font-size: 18px;
    }}
    .modal-content {{
        width: 98%;
        margin: 10px auto;
    }}
    .cart-item {{
        flex-direction: column;
        text-align: center;
    }}
    .cart-item-img {{
        margin-right: 0;
        margin-bottom: 15px;
    }}
    .scroll-to-top {{
        bottom: 20px;
        right: 20px;
        width: 45px;
        height: 45px;
    }}
}}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>Capital Restoration Catalog</h1>
        <p>Quality Furniture • Charity Proceeds • Free Removal Services</p>
        <div class="retail-notice">Prices shown are retail prices</div>
    </div>


    <div class="gallery-container">
        <input type="text" id="searchInput" onkeyup="filterProducts()" placeholder="Search products..." class="search-bar">
        <div class="gallery" id="gallery"></div>
        <div class="pagination-container" id="paginationContainer"></div>
    </div>


    <!-- Product Modal -->
    <div id="modal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal()">&times;</span>
            <div class="left-column">
                <div class="slideshow-container">
                    <div class="slideshow" id="slideshow"></div>
                    <div class="image-nav">
                        <button class="prev" onclick="changeSlide(-1)">&#10094;</button>
                        <button class="next" onclick="changeSlide(1)">&#10095;</button>
                    </div>
                </div>
                <div class="slide-info" id="slideInfo"></div>
            </div>
            <div class="right-column">
                <h2 id="modalTitle"></h2>
                <div class="modal-price" id="modalPrice"></div>
                <div class="modal-retail-note">Discounted price</div>
                <button class="modal-add-to-cart" id="modalAddToCart">Add to Inquiry List</button>
                <a href="#" class="contact-btn" id="modalEmailBtn">Email Inquiry (uses your cart)</a>
                <div class="description" id="modalDescription"></div>
            </div>
        </div>
    </div>


    <!-- Cart Modal -->
    <div id="cartModal" class="cart-modal">
        <div class="cart-content">
            <h2 class="cart-title">Your Inquiry List</h2>
            <div class="cart-items" id="cartItems">
                <div class="empty-cart">Your inquiry list is empty</div>
            </div>
            <div class="cart-total">Total: <span id="cartTotal">$0.00</span></div>
            <div class="cart-actions">
                <button class="cart-btn continue-shopping" onclick="closeCartModal()">Continue Shopping</button>
                <a href="#" class="cart-btn email-inquiry" id="emailInquiryBtn">Email Inquiry</a>
            </div>
        </div>
    </div>


    <div class="cart-indicator" id="cartIndicator" onclick="openCartModal()">0</div>
    <div class="scroll-to-top" id="scrollToTop" onclick="scrollToTop()">↑</div>


    <footer>
        <div class="footer-title">Capital Restoration</div>
        <div class="footer-divider"></div>
        <div style="margin-bottom:15px;">
            <strong>Contact:</strong>
            <a href="mailto:CapitalRestorationNewYork@gmail.com">CapitalRestorationNewYork@gmail.com</a>
        </div>
        <div style="margin-bottom:15px;">
            <strong>Location:</strong> 126 Madison Avenue, New York, NY 10006
        </div>
        <div>
            All proceeds go to charity. We are a registered non-profit (501c3).<br>
            Need free furniture removal services? Email us!
        </div>
        <div class="footer-note">
            Note: All prices shown are retail prices
        </div>
    </footer>
</div>


<script>
const products = {json.dumps(all_products)};
let filteredProducts = [...products];
let currentPage = 1;
const productsPerPage = {PRODUCTS_PER_PAGE};
const maxVisiblePages = 5;


// Cart state (persisted)
let cart = [];
const CART_KEY = 'capital_restoration_cart_v1';


function loadCart() {{
    try {{
        const raw = localStorage.getItem(CART_KEY);
        cart = raw ? JSON.parse(raw) : [];
        if (!Array.isArray(cart)) cart = [];
    }} catch (e) {{
        cart = [];
    }}
}}
function saveCart() {{
    try {{
        localStorage.setItem(CART_KEY, JSON.stringify(cart));
    }} catch (e) {{}}
}}
loadCart();


// Elements
const cartIndicator = document.getElementById('cartIndicator');
const cartItems = document.getElementById('cartItems');
const cartTotal = document.getElementById('cartTotal');
const emailInquiryBtn = document.getElementById('emailInquiryBtn');


const gallery = document.getElementById('gallery');
const paginationContainer = document.getElementById('paginationContainer');
const modal = document.getElementById('modal');
const slideshow = document.getElementById('slideshow');
const modalTitle = document.getElementById('modalTitle');
const modalPrice = document.getElementById('modalPrice');
const modalDescription = document.getElementById('modalDescription');
const slideInfo = document.getElementById('slideInfo');
const modalAddToCart = document.getElementById('modalAddToCart');
const modalEmailBtn = document.getElementById('modalEmailBtn');
const scrollToTopBtn = document.getElementById('scrollToTop');
let currentSlide = 0;
let currentProduct = 0;
let currentProductId = null;


// ------------------
// Cart Functions
// ------------------
function updateCartIndicator() {{
    cartIndicator.textContent = cart.length;
    cartIndicator.style.display = 'flex';
}}


function addToCart(productId) {{
    const product = products.find(p => p.id === productId);
    if (product && !cart.some(item => item.id === productId)) {{
        cart.push(product);
        saveCart();
        updateCartIndicator();
        updateCartModal();
        return true;
    }}
    return false;
}}


function removeFromCart(productId) {{
    const index = cart.findIndex(item => item.id === productId);
    if (index !== -1) {{
        cart.splice(index, 1);
        saveCart();
        updateCartIndicator();
        updateCartModal();
        return true;
    }}
    return false;
}}


function formatMoney(n) {{
    try {{ return n.toLocaleString('en-US', {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }}); }}
    catch(e) {{ return (Math.round(n*100)/100).toFixed(2); }}
}}


function buildCartMailtoLink() {{
    const subject = cart.length > 0
        ? `Inquiry about ${{cart.length}} product${{cart.length > 1 ? 's' : ''}}`
        : 'Product Inquiry';


    // Build plain text cleanly, then encode ONCE
    let lines = [];
    lines.push('Hello Capital Restoration,');
    lines.push('');
    if (cart.length > 0) {{
        lines.push("I'd like to inquire about:");
        cart.forEach(item => {{
            lines.push(`- ${{item.name}}`);
            lines.push(`  Price: $${{formatMoney(item.retail_price)}}`);
        }});
        const total = cart.reduce((sum, i) => sum + (i.retail_price || 0), 0);
        lines.push('');
        lines.push(`Total: $${{formatMoney(total)}}`);
    }} else {{
        lines.push("I'd like to inquire about the following product(s):");
    }}
    lines.push('');
    lines.push('Name:');
    lines.push('Phone:');
    lines.push('Preferred contact method:');
    lines.push('Notes:');
    const body = lines.join('\n');


    return `mailto:CapitalRestorationNewYork@gmail.com?subject=${{encodeURIComponent(subject)}}&body=${{encodeURIComponent(body)}}`;
}}


function updateCartModal() {{
    if (cart.length === 0) {{
        cartItems.innerHTML = '<div class="empty-cart">Your inquiry list is empty</div>';
        cartTotal.textContent = '$0.00';
        emailInquiryBtn.style.display = 'none';
        return;
    }}
    emailInquiryBtn.style.display = 'inline-block';
    let total = 0;
    let itemsHTML = '';


    cart.forEach(item => {{
        total += (item.retail_price || 0);
        itemsHTML += `
            <div class="cart-item">
                <img src="${{item.image_urls && item.image_urls[0] ? item.image_urls[0] : ''}}" alt="${{item.name}}" class="cart-item-img">
                <div class="cart-item-details">
                    <div class="cart-item-name">${{item.name}}</div>
                    <div class="cart-item-price">$${{formatMoney(item.retail_price || 0)}} </div>
                </div>
                <button class="remove-from-cart" onclick="removeFromCart(${{item.id}})">×</button>
            </div>
        `;
    }});


    cartItems.innerHTML = itemsHTML;
    cartTotal.textContent = '$' + formatMoney(total);


    // Update email link (cart modal button)
    emailInquiryBtn.href = buildCartMailtoLink();
}}


function openCartModal() {{
    document.getElementById('cartModal').classList.add('show');
    document.body.style.overflow = 'hidden';
}}


function closeCartModal() {{
    document.getElementById('cartModal').classList.remove('show');
    document.body.style.overflow = 'auto';
}}


// ------------------
// Render gallery
// ------------------
function renderGallery() {{
    gallery.innerHTML = '';
    const start = (currentPage - 1) * productsPerPage;
    const end = start + productsPerPage;
    const pageProducts = filteredProducts.slice(start, end);


    pageProducts.forEach((product, index) => {{
        const card = document.createElement('div');
        card.className = 'product-card';
        card.onclick = () => openModal(start + index);


        const img = document.createElement('img');
        img.src = (product.image_urls && product.image_urls[0]) ? product.image_urls[0] : '';
        img.alt = product.name;
        img.loading = 'lazy';


        const addToCartBtn = document.createElement('div');
        addToCartBtn.className = 'add-to-cart-btn';
        addToCartBtn.innerHTML = '+';
        addToCartBtn.onclick = (e) => {{
            e.stopPropagation();
            if (addToCart(product.id)) {{
                addToCartBtn.classList.add('added');
                setTimeout(() => addToCartBtn.classList.remove('added'), 800);
            }}
        }};


        const info = document.createElement('div');
        info.className = 'product-info';
        info.innerHTML = `
            <div class="product-name">${{product.name}}</div>
            <div class="product-price">$${{formatMoney(product.retail_price || 0)}}</div>
            <div class="product-retail-note">Price</div>
        `;


        card.appendChild(img);
        card.appendChild(addToCartBtn);
        card.appendChild(info);
        gallery.appendChild(card);
    }});


    renderPagination();
}}


// ------------------
// Pagination (First/Prev/Numbers/Next/Last + Go to Page)
// ------------------
function renderPagination() {{
    paginationContainer.innerHTML = '';
    const numPages = Math.ceil(filteredProducts.length / productsPerPage);
    if (numPages <= 1) return;


    const controls = document.createElement('div');
    controls.className = 'pagination-controls';


    // First
    const firstBtn = document.createElement('button');
    firstBtn.className = 'pagination-btn';
    firstBtn.textContent = 'First';
    firstBtn.disabled = currentPage === 1;
    firstBtn.onclick = () => {{ currentPage = 1; renderGallery(); window.scrollTo(0,0); }};
    controls.appendChild(firstBtn);


    // Prev
    const prevBtn = document.createElement('button');
    prevBtn.className = 'pagination-btn';
    prevBtn.textContent = '← Previous';
    prevBtn.disabled = currentPage === 1;
    prevBtn.onclick = () => {{
        if (currentPage > 1) {{
            currentPage--;
            renderGallery();
            window.scrollTo(0,0);
        }}
    }};
    controls.appendChild(prevBtn);


    // Page numbers
    const numbersContainer = document.createElement('div');
    numbersContainer.className = 'pagination-numbers';


    let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(numPages, startPage + maxVisiblePages - 1);
    if (endPage - startPage + 1 < maxVisiblePages) {{
        startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }}


    for (let i = startPage; i <= endPage; i++) {{
        const btn = document.createElement('button');
        btn.className = 'page-btn' + (i === currentPage ? ' active' : '');
        btn.innerText = i;
        btn.onclick = () => {{ currentPage = i; renderGallery(); window.scrollTo(0,0); }};
        numbersContainer.appendChild(btn);
    }}
    controls.appendChild(numbersContainer);


    // Next
    const nextBtn = document.createElement('button');
    nextBtn.className = 'pagination-btn';
    nextBtn.textContent = 'Next →';
    nextBtn.disabled = currentPage === numPages;
    nextBtn.onclick = () => {{
        if (currentPage < numPages) {{
            currentPage++;
            renderGallery();
            window.scrollTo(0,0);
        }}
    }};
    controls.appendChild(nextBtn);


    // Last
    const lastBtn = document.createElement('button');
    lastBtn.className = 'pagination-btn';
    lastBtn.textContent = 'Last';
    lastBtn.disabled = currentPage === numPages;
    lastBtn.onclick = () => {{ currentPage = numPages; renderGallery(); window.scrollTo(0,0); }};
    controls.appendChild(lastBtn);


    // Go to page
    const gotoWrap = document.createElement('div');
    gotoWrap.className = 'goto-wrapper';
    const gotoInput = document.createElement('input');
    gotoInput.className = 'goto-input';
    gotoInput.type = 'number';
    gotoInput.placeholder = 'Go to page';
    gotoInput.min = 1;
    gotoInput.max = numPages;
    gotoInput.value = currentPage;


    const gotoBtn = document.createElement('button');
    gotoBtn.className = 'goto-button';
    gotoBtn.textContent = 'Go';
    function gotoHandler() {{
        let val = parseInt(gotoInput.value, 10);
        if (isNaN(val)) return;
        val = Math.max(1, Math.min(numPages, val));
        currentPage = val;
        renderGallery();
        window.scrollTo(0,0);
    }}
    gotoBtn.onclick = gotoHandler;
    gotoInput.onkeydown = (e) => {{
        if (e.key === 'Enter') gotoHandler();
    }};


    gotoWrap.appendChild(gotoInput);
    gotoWrap.appendChild(gotoBtn);
    controls.appendChild(gotoWrap);


    paginationContainer.appendChild(controls);
}}


// ------------------
// Search
// ------------------
function filterProducts() {{
    const query = document.getElementById('searchInput').value.toLowerCase();
    filteredProducts = products.filter(p => p.name.toLowerCase().includes(query));
    currentPage = 1;
    renderGallery();
}}


// ------------------
// Modal Slideshow
// ------------------
function openModal(index) {{
    currentProduct = index;
    loadProductModal(currentProduct);
    modal.classList.add('show');
    document.body.style.overflow = 'hidden';
}}


function loadProductModal(index) {{
    slideshow.innerHTML = '';
    const product = filteredProducts[index];
    currentProductId = product.id;
    modalTitle.innerText = product.name;
    modalPrice.innerText = '$' + formatMoney(product.retail_price || 0);
    modalDescription.innerText = product.description || '';


    // Add-to-cart button state
    if (cart.some(item => item.id === product.id)) {{
        modalAddToCart.textContent = 'In Inquiry List';
        modalAddToCart.classList.add('added');
    }} else {{
        modalAddToCart.textContent = 'Add to Inquiry List';
        modalAddToCart.classList.remove('added');
    }}


    // Images
    (product.image_urls || []).forEach((url, i) => {{
        let img = document.createElement('img');
        img.src = url;
        img.alt = product.name + ' - Image ' + (i + 1);
        if (i === 0) img.classList.add('active');
        slideshow.appendChild(img);
    }});


    currentSlide = 0;
    updateSlideInfo();
}}


function closeModal() {{
    modal.classList.remove('show');
    document.body.style.overflow = 'auto';
}}


function changeSlide(n) {{
    const imgs = slideshow.getElementsByTagName('img');
    if (imgs.length === 0) return;
    imgs[currentSlide].classList.remove('active');
    currentSlide = (currentSlide + n + imgs.length) % imgs.length;
    imgs[currentSlide].classList.add('active');
    updateSlideInfo();
}}


function updateSlideInfo() {{
    const imgs = slideshow.getElementsByTagName('img');
    slideInfo.innerText = 'Image ' + (imgs.length ? (currentSlide + 1) : 0) + ' of ' + imgs.length;
}}


// Modal buttons
modalAddToCart.onclick = function(e) {{
    e.stopPropagation();
    if (currentProductId) {{
        if (addToCart(currentProductId)) {{
            modalAddToCart.textContent = 'In Inquiry List';
            modalAddToCart.classList.add('added');
        }}
    }}
}};


// IMPORTANT: Email Inquiry from the modal should ADD the product to cart first,
// then open an email for the ENTIRE CART with clean formatting.
modalEmailBtn.onclick = function(e) {{
    e.preventDefault();
    if (currentProductId) addToCart(currentProductId);
    // Refresh modal button state (in case it just got added)
    const already = cart.some(item => item.id === currentProductId);
    if (already) {{
        modalAddToCart.textContent = 'In Inquiry List';
        modalAddToCart.classList.add('added');
    }}
    const href = buildCartMailtoLink();
    window.location.href = href;
}};


// Close modals when clicking outside
modal.onclick = function(e) {{ if (e.target === modal) closeModal(); }};
document.getElementById('cartModal').onclick = function(e) {{
    if (e.target === this) closeCartModal();
}};


// Keyboard navigation
document.addEventListener('keydown', function(e) {{
    if (modal.classList.contains('show')) {{
        if (e.key === 'Escape') closeModal();
        if (e.key === 'ArrowLeft') changeSlide(-1);
        if (e.key === 'ArrowRight') changeSlide(1);
    }}
    if (document.getElementById('cartModal').classList.contains('show')) {{
        if (e.key === 'Escape') closeCartModal();
    }}
}});


// Scroll to top functionality
window.onscroll = function() {{
    if (document.body.scrollTop > 300 || document.documentElement.scrollTop > 300) {{
        scrollToTopBtn.classList.add('visible');
    }} else {{
        scrollToTopBtn.classList.remove('visible');
    }}
}};
function scrollToTop() {{
    window.scrollTo({{ top: 0, behavior: 'smooth' }});
}}


// Initial render
updateCartIndicator();
updateCartModal();
renderGallery();
</script>
</body>
</html>
"""


# -----------------------------
# Save HTML
# -----------------------------
with open(html_file, "w", encoding="utf-8") as f:
    f.write(html_str)


# -----------------------------
# Download HTML in Colab
# -----------------------------
try:
    from google.colab import files
    files.download(html_file)
except Exception:
    # If not in Colab, just print path
    print(f"Saved: {html_file}")