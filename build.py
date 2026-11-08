#!/usr/bin/env python3
"""Build a complete, offline-friendly academic homepage using only Python's stdlib."""
import html
import json
import re
import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROFILE = ROOT / "data" / "profile.json"


def esc(value):
    return html.escape(str(value), quote=True)


def link(url, label, extra=""):
    external = ' target="_blank" rel="noopener noreferrer"' if url.startswith(("https://", "http://")) else ""
    return f'<a href="{esc(url)}"{external}{extra}>{label}</a>'


def inline_text(value):
    """Allow bold emphasis in profile prose while escaping all HTML."""
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", esc(value))


def icon(name):
    shapes = {
        "email": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 6 9 7 9-7"/>',
        "scholar": '<path d="m2 9 10-6 10 6-10 6-10-6Zm4 3v5c4 3 8 3 12 0v-5m4-3v8"/>',
        "github": '<path d="M9 19c-4.3 1.4-4.3-2.5-6-3m12 6v-3.9a3.4 3.4 0 0 0-.9-2.7c3-.3 6.2-1.5 6.2-6.7A5.3 5.3 0 0 0 19 5a5 5 0 0 0-.1-3.5s-1.2-.4-3.9 1.5a13.4 13.4 0 0 0-7 0C5.3 1.1 4.1 1.5 4.1 1.5A5 5 0 0 0 4 5a5.3 5.3 0 0 0-1.3 3.7c0 5.2 3.2 6.4 6.2 6.7a3.4 3.4 0 0 0-.9 2.7V22"/>',
        "orcid": '<circle cx="12" cy="12" r="10"/><path d="M7 10v7m0-10h.01M11 8h3a4.5 4.5 0 0 1 0 9h-3V8Z"/>',
    }
    return f'<svg class="icon icon-{esc(name)}" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">{shapes[name]}</svg>'


def author_list(authors, name):
    result = []
    for author in authors:
        plain = author.rstrip("*†")
        suffix = author[len(plain):]
        label = f'<strong>{esc(plain)}</strong>' if plain == name else esc(plain)
        if suffix:
            label += f'<sup>{esc(suffix)}</sup>'
        result.append(label)
    return ", ".join(result)


def publication(p, name):
    published = p["status"] == "published"
    title = link(p["paper"], esc(p["title"])) if p.get("paper") else esc(p["title"])
    venue_name = p["venue_full"].removeprefix("Proceedings of the ")
    meta = ("" if published else '<span class="venue-note">Submitted to </span>')
    meta += f'<em class="venue">{esc(venue_name)} <span class="venue-abbreviation">({esc(p["venue"])})</span></em>'
    if published:
        meta += f', {esc(p["year"])}'
    if not published:
        status = "Major revision" if p["status"] == "major_revision" else "Under review"
        meta += f'<span class="manuscript-status"> · {status}</span>'
    if published and p.get("venue_note"):
        meta += f'<span class="venue-note"> · {esc(p["venue_note"])}</span>'
    actions = []
    for key in ("paper", "code"):
        label = f'[{key}]'
        if p.get(key):
            actions.append(link(p[key], label, f' aria-label="{esc(key.capitalize() + ": " + p["title"])}"'))
        else:
            actions.append(f'<span class="unavailable-link" aria-disabled="true" title="{key.capitalize()} link not yet available">{label}</span>')
    separator = '<span class="action-divider" aria-hidden="true"> / </span>'
    action_html = '<div class="paper-actions">' + separator.join(actions) + '</div>'
    return f'''<li class="publication" id="paper-{esc(p['id'])}">
      <div class="paper-content">
        <h3 class="paper-title">{title}</h3>
        <p class="authors">{author_list(p['authors'], name)}</p>
        <p class="paper-meta">{meta}</p>
        {action_html}
      </div>
    </li>'''


def build():
    data = json.loads(PROFILE.read_text(encoding="utf-8"))
    papers = data["publications"]
    ids = [p["id"] for p in papers]
    if len(set(ids)) != len(ids) or any(not re.fullmatch(r"[a-z0-9-]+", i) for i in ids):
        raise ValueError("Publication IDs must be unique and use lowercase letters, numbers, and hyphens.")
    valid_statuses = {"published", "under_review", "major_revision"}
    if any(p["status"] not in valid_statuses for p in papers):
        raise ValueError("Use published, under_review, or major_revision for publication status.")
    published = [p for p in papers if p["status"] == "published"]
    manuscripts = [p for p in papers if p["status"] != "published"]
    advisors = " and ".join(esc(a["title"]) + " " + link(a["url"], esc(a["name"])) for a in data["advisors"])
    contact_links = [link("mailto:" + data["email"], icon("email") + '<span>Email</span>')]
    for key, label in [("scholar", "Google Scholar"), ("github", "GitHub"), ("orcid", "ORCID")]:
        if data["links"].get(key):
            contact_links.append(link(data["links"][key], icon(key) + f'<span>{esc(label)}</span>'))
    publication_html = "\n".join(publication(p, data["name"]) for p in papers)
    disclosure_groups = []
    for category in ("CVE", "CNVD"):
        records = [v for v in data["vulnerabilities"] if v["id"].startswith(category + "-")]
        identifiers = "".join(
            '<li>' + (link(v["url"], esc(v["id"])) if v.get("url") else esc(v["id"])) + '</li>'
            for v in records
        )
        disclosure_groups.append(f'<div class="disclosure-group"><dt>{category}</dt><dd><ul class="vulnerability-list">{identifiers}</ul></dd></div>')
    vulnerabilities = "\n".join(disclosure_groups)
    services = "\n".join(f'<li><div class="list-entry"><span>{esc(s["name"])} <span class="muted">({esc(s["short"])})</span></span><time>{esc(s["year"])}</time></div></li>' for s in data["services"])
    awards = "\n".join(f'<li><div class="list-entry"><div><strong>{esc(a["name"])}</strong><p class="muted">{esc(a["detail"])}</p></div><span class="timeline-date">{esc(a["year"])}</span></div></li>' for a in data["awards"])
    description = f"{data['name']} — {data['role']} at {data['institution_short']}. Binary analysis, reverse engineering, and LLM agents for software engineering."
    portrait = ""
    if data.get("photo"):
        photo = Path(data["photo"])
        if photo.is_absolute() or ".." in photo.parts or not photo.parts or photo.parts[0] != "assets" or not (ROOT / photo).is_file():
            raise ValueError("photo must reference an existing image inside assets/.")
        portrait = f'<figure class="portrait"><img src="{esc(data["photo"])}" alt="{esc(data.get("photo_alt", data["name"]))}" width="320" height="320" fetchpriority="high"></figure>'
    content = f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{esc(description)}">
  <meta name="theme-color" content="#ffffff">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{esc(data['name'])} | Academic Homepage">
  <meta property="og:description" content="{esc(description)}">
  <title>{esc(data['name'])} | Binary Analysis &amp; LLM Agents</title>
  <link rel="icon" type="image/svg+xml" href="assets/favicon.svg">
  <link rel="preload" href="assets/fonts/lato-regular.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="stylesheet" href="assets/styles.css">
</head>
<body>
  <a class="skip-link" href="#main">Skip to content</a>
  <header class="site-header">
    <nav aria-label="Main navigation">
      <a href="#about">About</a><a href="#publications">Publications</a><a href="#security">Disclosures</a><a href="#service">Service</a>
    </nav>
  </header>
  <main id="main">
    <section class="hero{' hero-with-photo' if portrait else ''}" id="about" aria-labelledby="name">
      {portrait}
      <div class="hero-copy">
      <h1 id="name">{esc(data['name'])}</h1>
      <p class="slogan">{esc(data['slogan'])}</p>
      <div class="biography">
        <p>I am a {esc(data['study_year'])} master’s student in the {esc(data['school'])} at the <a href="https://en.ustc.edu.cn/" target="_blank" rel="noopener noreferrer">{esc(data['institution'])}</a> ({esc(data['institution_short'])}), advised by {advisors}.</p>
        <p>{inline_text(data['research_statement'])}</p>
        <p>{inline_text(data['engineering_statement'])}</p>
        <p><strong>{esc(data['phd_statement'])}</strong> Please feel free to {link('mailto:' + data['email'], 'contact me')}.</p>
      </div>
      <div class="contact-links">{''.join(contact_links)}</div>
      </div>
    </section>

    <section class="section publications-section" id="publications" aria-labelledby="publications-title">
      <div class="section-heading">
        <h2 id="publications-title">Publications</h2>
      </div>
      <p class="section-note">* Equal contribution <span aria-hidden="true">·</span> † Corresponding author</p>
      <ul class="publication-list" id="publication-list">
        {publication_html}
      </ul>
    </section>

    <section class="section" id="security" aria-labelledby="security-title">
      <div class="section-heading"><h2 id="security-title">Vulnerability Disclosures</h2></div>
      <p class="section-intro">{esc(data['security_statement'])}</p>
      <dl class="disclosure-groups">{vulnerabilities}</dl>
    </section>

    <section class="section" id="service" aria-labelledby="service-title">
      <div class="section-heading"><h2 id="service-title">Academic Service</h2><span class="section-aside">Reviewer</span></div>
      <ul class="service-list">{services}</ul>
    </section>

    <section class="section" id="honors" aria-labelledby="honors-title">
      <div class="section-heading"><h2 id="honors-title">Selected Honors</h2></div>
      <ul class="awards-list">{awards}</ul>
    </section>

    <section class="contact-footer" aria-label="Contact">
      <p>Let’s talk research.</p>
      {link('mailto:' + data['email'], icon('email') + f'<span>{esc(data["email"])}</span>')}
    </section>
  </main>
  <footer class="site-footer"><span>© 2026 {esc(data['name'])}<span class="footer-location"> · {esc(data['location'])}</span></span><span>Updated {esc(data['updated'])}</span></footer>
</body>
</html>
'''
    target = ROOT / "index.html"
    temporary = ROOT / ".index.html.tmp"
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(target)
    print(f"Built index.html: {len(published)} published/accepted papers, {len(manuscripts)} manuscripts.")
    return target


def export_site(destination):
    """Export only website files, excluding source data and local preview state."""
    target = Path(destination).resolve()
    if target == ROOT or ROOT.is_relative_to(target):
        raise ValueError("Choose a separate output folder, not the project root or a parent.")
    target.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "index.html", target / "index.html")
    shutil.copy2(ROOT / ".nojekyll", target / ".nojekyll")
    shutil.copytree(ROOT / "assets", target / "assets", dirs_exist_ok=True)
    print(f"Exported website to {target}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build Li Hu's academic homepage.")
    parser.add_argument("--output-dir", help="Also export the website files to this directory.")
    args = parser.parse_args()
    build()
    if args.output_dir:
        export_site(args.output_dir)
