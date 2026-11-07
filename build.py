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


def bibtex(paper):
    first = paper["authors"][0].rstrip("*†").split()[-1].lower()
    key = f'{first}{paper["year"]}{paper["id"].replace("-", "")}'
    kind = paper.get("type", "inproceedings")
    venue_field = "journal" if kind == "article" else "booktitle"
    fields = [
        ("title", "{" + paper["title"] + "}"),
        ("author", " and ".join(a.rstrip("*†") for a in paper["authors"])),
        (venue_field, paper["venue_full"]),
        ("year", str(paper["year"]))
    ]
    if paper.get("doi"):
        fields.append(("doi", paper["doi"]))
    if paper.get("paper"):
        fields.append(("url", paper["paper"]))
    return f"@{kind}{{{key},\n" + ",\n".join(f"  {field} = {{{value}}}" for field, value in fields) + "\n}\n"


def publication(p, name, index):
    published = p["status"] == "published"
    title = link(p["paper"], esc(p["title"])) if p.get("paper") else esc(p["title"])
    meta = f'<span class="venue">{esc(p["venue"])} {p["year"]}</span>' if published else '<span class="manuscript-status">' + ("Major revision" if p["status"] == "major_revision" else "Under review") + "</span>"
    if published and p.get("venue_note"):
        meta += f'<span class="venue-note"> · {esc(p["venue_note"])}</span>'
    actions = []
    if p.get("paper"):
        actions.append(link(p["paper"], 'Paper <span aria-hidden="true">↗</span>'))
    if p.get("code"):
        actions.append(link(p["code"], 'Code <span aria-hidden="true">↗</span>'))
    if published:
        actions.append(f'<a class="citation-link" href="assets/bibtex/{esc(p["id"])}.bib" data-citation="{esc(p["id"])}" download>BibTeX</a>')
    summary = f'<p class="paper-summary">{esc(p["summary"])}</p>' if p.get("summary") else ""
    action_html = '<div class="paper-actions">' + '<span aria-hidden="true" class="action-separator">/</span>'.join(actions) + '</div>' if actions else ""
    return f'''<li class="publication" id="paper-{esc(p['id'])}" data-selected="{str(bool(p.get('selected'))).lower()}">
      <span class="paper-index" aria-hidden="true">{index:02d}</span>
      <div class="paper-content">
        <h3 class="paper-title">{title}</h3>
        <p class="authors">{author_list(p['authors'], name)}</p>
        <p class="paper-meta">{meta}</p>
{summary}{action_html}
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
    selected = sum(bool(p.get("selected")) for p in published)
    bib_dir = ROOT / "assets" / "bibtex"
    bib_dir.mkdir(parents=True, exist_ok=True)
    for stale in bib_dir.glob("*.bib"):
        if stale.stem not in {p["id"] for p in published}:
            stale.unlink()
    citations = {}
    for paper in published:
        text = bibtex(paper)
        (bib_dir / (paper["id"] + ".bib")).write_text(text, encoding="utf-8")
        citations[paper["id"]] = {"title": paper["title"], "bibtex": text}
    citation_json = json.dumps(citations, ensure_ascii=False).replace("<", "\\u003c")
    advisors = " and ".join(esc(a["title"]) + " " + link(a["url"], esc(a["name"])) for a in data["advisors"])
    contact_links = [link("mailto:" + data["email"], 'Email <span aria-hidden="true">↗</span>'), link(data["links"]["cv"], 'Curriculum Vitae <span aria-hidden="true">↗</span>', ' target="_blank"')]
    for key, label in [("scholar", "Google Scholar"), ("github", "GitHub"), ("orcid", "ORCID")]:
        if data["links"].get(key):
            contact_links.append(link(data["links"][key], esc(label) + ' <span aria-hidden="true">↗</span>'))
    interests = '<span class="interest-divider" aria-hidden="true">/</span>'.join(f'<span>{esc(i)}</span>' for i in data["research_interests"])
    publication_html = "\n".join(publication(p, data["name"], i + 1) for i, p in enumerate(published))
    manuscript_html = "\n".join(publication(p, data["name"], i + 1) for i, p in enumerate(manuscripts))
    vulnerabilities = "\n".join(f'''<li class="vulnerability">
      <div class="vulnerability-heading">{link(v['url'], esc(v['id']))}<span class="severity">CVSS {esc(v['score'])} · Critical</span></div>
      <p>{esc(v['product'])} — {esc(v['description'])}</p>
    </li>''' for v in data["vulnerabilities"])
    other_cves = ", ".join(esc(v) for v in data["other_vulnerabilities"])
    education = "\n".join(f'''<li class="timeline-item"><div><h3>{esc(e['institution'])}</h3><p>{esc(e['degree'])}</p><p class="muted education-detail">{esc(e['detail'])}</p></div><span class="timeline-date">{esc(e['dates'])}</span></li>''' for e in data["education"])
    services = "\n".join(f'<li><span>{esc(s["name"])} <span class="muted">({esc(s["short"])})</span></span><time>{esc(s["year"])}</time></li>' for s in data["services"])
    awards = "\n".join(f'<li><div><strong>{esc(a["name"])}</strong><p class="muted">{esc(a["detail"])}</p></div><span class="timeline-date">{esc(a["year"])}</span></li>' for a in data["awards"])
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
  <meta name="theme-color" content="#fbfaf7">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{esc(data['name'])} | Academic Homepage">
  <meta property="og:description" content="{esc(description)}">
  <title>{esc(data['name'])} | Binary Analysis &amp; LLM Agents</title>
  <link rel="icon" type="image/svg+xml" href="assets/favicon.svg">
  <link rel="stylesheet" href="assets/styles.css">
  <script src="assets/site.js" defer></script>
</head>
<body>
  <a class="skip-link" href="#main">Skip to content</a>
  <header class="site-header">
    <a class="wordmark" href="#about" aria-label="{esc(data['name'])}, back to introduction">{esc(data['name'])}<span class="wordmark-dot">.</span></a>
    <nav aria-label="Main navigation">
      <a href="#about">About</a><a href="#publications">Publications</a><a href="#security">Security</a><a href="#background">Background</a>
    </nav>
  </header>
  <main id="main">
    <section class="hero{' hero-with-photo' if portrait else ''}" id="about" aria-labelledby="name">
      <div class="hero-copy">
      <p class="eyebrow">{esc(data['role'])}<span aria-hidden="true"> · </span>{esc(data['institution_short'])}</p>
      <h1 id="name">{esc(data['name'])}</h1>
      <p class="slogan">{esc(data['slogan'])}</p>
      <div class="biography">
        <p>I am a {esc(data['study_year'])} master’s student in the {esc(data['school'])} at the <a href="https://en.ustc.edu.cn/" target="_blank" rel="noopener noreferrer">{esc(data['institution'])}</a> ({esc(data['institution_short'])}), advised by {advisors}.</p>
        <p>{esc(data['research_statement'])}</p>
        <p><strong>{esc(data['phd_statement'])}</strong> Please feel free to {link('mailto:' + data['email'], 'contact me')}.</p>
      </div>
      <div class="interest-line" aria-label="Research interests">{interests}</div>
      <div class="contact-links">{''.join(contact_links)}</div>
      </div>
      {portrait}
    </section>

    <section class="section publications-section" id="publications" aria-labelledby="publications-title">
      <div class="section-heading">
        <h2 id="publications-title">Publications</h2>
        <div class="publication-filters" aria-label="Filter published papers" hidden>
          <button type="button" data-filter="selected" aria-pressed="false">Selected <span>{selected}</span></button>
          <button type="button" data-filter="all" aria-pressed="true">All <span>{len(published)}</span></button>
        </div>
      </div>
      <p class="section-note">* Equal contribution <span aria-hidden="true">·</span> † Corresponding author</p>
      <p class="sr-only" id="filter-status" role="status" aria-live="polite"></p>
      <ol class="publication-list" id="published-list">
        {publication_html}
      </ol>
      <details class="manuscripts">
        <summary><span>Manuscripts</span><span class="manuscript-count">{len(manuscripts)}</span><span class="details-label">Under review &amp; major revision</span><span class="details-plus" aria-hidden="true">+</span></summary>
        <ol class="publication-list manuscript-list">{manuscript_html}</ol>
      </details>
    </section>

    <section class="section" id="security" aria-labelledby="security-title">
      <div class="section-heading"><h2 id="security-title">Security Research</h2><span class="section-aside">Selected disclosures</span></div>
      <p class="section-intro">Alongside my academic research, I discover and report vulnerabilities in real-world software and embedded devices.</p>
      <ul class="vulnerability-list">{vulnerabilities}</ul>
      <details class="other-disclosures"><summary>More confirmed vulnerabilities <span aria-hidden="true">↗</span></summary><p>{other_cves}</p></details>
    </section>

    <section class="section" id="background" aria-labelledby="education-title">
      <div class="section-heading"><h2 id="education-title">Education</h2></div>
      <ul class="timeline">{education}</ul>
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
      {link('mailto:' + data['email'], esc(data['email']) + ' <span aria-hidden="true">↗</span>')}
    </section>
  </main>
  <footer class="site-footer"><span>© 2026 {esc(data['name'])}<span class="footer-location"> · {esc(data['location'])}</span></span><span>Updated {esc(data['updated'])}</span></footer>

  <dialog id="citation-dialog" aria-labelledby="citation-title">
    <div class="dialog-heading"><h2 id="citation-title">BibTeX citation</h2><button type="button" class="close-dialog" aria-label="Close citation dialog">×</button></div>
    <p id="citation-paper"></p><pre><code id="citation-content"></code></pre>
    <div class="dialog-actions"><button type="button" id="copy-citation">Copy citation</button><span id="copy-status" role="status" aria-live="polite"></span></div>
  </dialog>
  <script type="application/json" id="citation-data">{citation_json}</script>
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
