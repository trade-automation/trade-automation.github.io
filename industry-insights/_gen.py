#!/usr/bin/env python3
import os, json, sys

OUTPUT_DIR = "/Coze/Drive/Elias/所有对话/主对话/foshanffe-site/industry-insights/"
sys.path.insert(0, OUTPUT_DIR)

def get_css():
    return """<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap');
:root{--navy:#1B2A4A;--gold:#C9A96E;--warm-white:#FAF8F5;--text:#333;--text-light:#666;--border:#e8e4df}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',sans-serif;color:var(--text);background:#fff;line-height:1.7}
.nav{position:fixed;top:0;width:100%;background:var(--navy);z-index:1000;padding:0 40px;display:flex;align-items:center;justify-content:space-between;height:64px;box-shadow:0 2px 12px rgba(0,0,0,.15)}
.nav-brand{font-family:'Playfair Display',serif;font-size:1.4rem;color:var(--gold);text-decoration:none;font-weight:700}
.nav-links{display:flex;gap:24px;list-style:none}
.nav-links a{color:#fff;text-decoration:none;font-size:.85rem;font-weight:500;letter-spacing:.3px;transition:color .3s}
.nav-links a:hover{color:var(--gold)}
.article-header{background:linear-gradient(135deg,var(--navy) 0%,#2a3f6b 100%);padding:120px 40px 60px;text-align:center}
.article-category{display:inline-block;background:var(--gold);color:var(--navy);padding:6px 18px;border-radius:20px;font-size:.75rem;font-weight:600;text-transform:uppercase;letter-spacing:1px;margin-bottom:20px}
.article-header h1{font-family:'Playfair Display',serif;font-size:2.6rem;color:#fff;max-width:800px;margin:0 auto 16px;line-height:1.25}
.article-meta{color:rgba(255,255,255,.7);font-size:.9rem}
.article-body{max-width:800px;margin:0 auto;padding:60px 24px 80px;font-size:1.05rem;line-height:1.85;color:var(--text)}
.article-body h2{font-family:'Playfair Display',serif;font-size:1.7rem;color:var(--navy);margin:48px 0 18px;line-height:1.3}
.article-body h3{font-family:'Playfair Display',serif;font-size:1.3rem;color:var(--navy);margin:36px 0 14px}
.article-body p{margin-bottom:20px;color:#444}
.article-body ul,.article-body ol{margin:0 0 20px 24px}
.article-body li{margin-bottom:10px;color:#444}
.article-body strong{color:var(--navy)}
.article-body a{color:var(--gold);text-decoration:underline}
.highlight-box{background:var(--warm-white);border-left:4px solid var(--gold);padding:24px 28px;margin:32px 0;border-radius:0 8px 8px 0}
.newsletter{background:var(--navy);padding:80px 40px;text-align:center}
.newsletter h2{font-family:'Playfair Display',serif;color:#fff;font-size:1.8rem;margin-bottom:12px}
.newsletter p{color:rgba(255,255,255,.7);margin-bottom:28px;font-size:1rem}
.newsletter form{display:flex;gap:12px;justify-content:center;flex-wrap:wrap}
.newsletter input[type="email"]{padding:14px 20px;border:none;border-radius:6px;font-size:1rem;width:320px;background:rgba(255,255,255,.12);color:#fff;outline:none}
.newsletter input[type="email"]::placeholder{color:rgba(255,255,255,.5)}
.newsletter button{padding:14px 32px;background:var(--gold);color:var(--navy);border:none;border-radius:6px;font-weight:600;font-size:1rem;cursor:pointer;transition:background .3s}
.newsletter button:hover{background:#b8954f}
.footer{background:#111;padding:48px 40px 24px;color:rgba(255,255,255,.6);font-size:.85rem}
.footer-grid{display:grid;grid-template-columns:2fr 1fr 1fr 1fr;gap:40px;max-width:1200px;margin:0 auto 36px}
.footer h4{color:var(--gold);font-size:.9rem;margin-bottom:14px;text-transform:uppercase;letter-spacing:1px}
.footer a{color:rgba(255,255,255,.6);text-decoration:none;display:block;margin-bottom:8px;transition:color .3s}
.footer a:hover{color:var(--gold)}
.footer-bottom{border-top:1px solid rgba(255,255,255,.1);padding-top:24px;text-align:center;max-width:1200px;margin:0 auto}
@media(max-width:768px){
.nav-links{display:none}
.article-header h1{font-size:1.8rem}
.article-header{padding:100px 20px 40px}
.footer-grid{grid-template-columns:1fr 1fr}
}
</style>"""

def get_nav():
    return """<nav class="nav">
<a href="/" class="nav-brand">foshanFFE.com</a>
<ul class="nav-links">
<li><a href="/services/casegoods.html">Casegoods</a></li>
<li><a href="/services/soft-seating.html">Soft Seating</a></li>
<li><a href="/services/lobby-furniture.html">Lobby</a></li>
<li><a href="/services/lighting.html">Lighting</a></li>
<li><a href="/services/mattress.html">Mattress</a></li>
<li><a href="/services/drapery.html">Drapery</a></li>
<li><a href="/services/bath-vanities.html">Vanities</a></li>
<li><a href="/industry-insights/">Industry Insights</a></li>
</ul>
</nav>"""

def get_newsletter():
    return """<section class="newsletter">
<h2>Stay Ahead in Hotel FF&E Sourcing</h2>
<p>Get weekly insights on hotel furniture trends, sourcing tips, and industry news delivered to your inbox.</p>
<form action="mailto:info@foshanFFE.com" method="post" enctype="text/plain">
<input type="email" name="email" placeholder="Enter your business email" required>
<button type="submit">Subscribe</button>
</form>
</section>"""

def get_footer():
    return """<footer class="footer">
<div class="footer-grid">
<div>
<h4>About Foshan FF&E</h4>
<p>Your single-source hospitality FF&E integrator. From guestroom casegoods to lobby furniture, lighting, mattress, drapery, and bath vanities — one PO, one supplier-of-record, from drawing to container.</p>
</div>
<div>
<h4>Services</h4>
<a href="/services/casegoods.html">Casegoods</a>
<a href="/services/soft-seating.html">Soft Seating</a>
<a href="/services/lobby-furniture.html">Lobby Furniture</a>
<a href="/services/lighting.html">Lighting</a>
<a href="/services/mattress.html">Mattress</a>
<a href="/services/drapery.html">Drapery &amp; Curtains</a>
<a href="/services/bath-vanities.html">Bath Vanities</a>
</div>
<div>
<h4>Resources</h4>
<a href="/industry-insights/">Industry Insights</a>
<a href="/projects.html">Case Studies</a>
<a href="/technical-documents/">Technical Documents</a>
<a href="/about.html">About Us</a>
</div>
<div>
<h4>Contact</h4>
<a href="mailto:info@foshanFFE.com">info@foshanFFE.com</a>
<p style="margin-top:8px">Foshan, Guangdong, China</p>
<p>Partnered with 19 specialist factories</p>
</div>
</div>
<div class="footer-bottom">
<p>&copy; 2026 foshanFFE.com — Hotel FF&E Sourcing Partner. All rights reserved.</p>
</div>
</footer>"""

def wrap_article(cat_slug, cat_label, title, date, desc, body_html):
    schema = json.dumps({
        "@context":"https://schema.org","@type":"Article",
        "headline":title,"datePublished":date,"dateModified":date,
        "description":desc,
        "author":{"@type":"Organization","name":"foshanFFE.com","url":"https://foshanffe.com"},
        "publisher":{"@type":"Organization","name":"foshanFFE.com","url":"https://foshanffe.com"}
    }, indent=2)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} | foshanFFE.com</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="https://foshanffe.com/industry-insights/{cat_slug}">
{get_css()}
<script type="application/ld+json">
{schema}
</script>
</head>
<body>
{get_nav()}
<header class="article-header">
<span class="article-category">{cat_label}</span>
<h1>{title}</h1>
<p class="article-meta">Published: {date} &middot; foshanFFE.com Editorial Team</p>
</header>
<main class="article-body">
{body_html}
</main>
{get_newsletter()}
{get_footer()}
</body>
</html>"""

from _article_bodies import articles_data

for filename, slug, cat_label, title, date, desc, body in articles_data:
    html = wrap_article(slug, cat_label, title, date, desc, body)
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    word_count = len(body.split())
    print(f"OK {filename} -- {word_count} words, {len(html):,} bytes")

print(f"\nDone. {len(articles_data)} articles generated.")
