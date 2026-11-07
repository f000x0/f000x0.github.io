"use strict";

// Content is rendered into index.html. JavaScript only adds optional interactions.
const filterBar = document.querySelector(".publication-filters");
const filterButtons = [...document.querySelectorAll("[data-filter]")];
const papers = [...document.querySelectorAll("#publication-list .publication")];
const filterStatus = document.querySelector("#filter-status");

function filterPapers(mode, announce = true) {
  let count = 0;
  papers.forEach((paper) => {
    const show = mode === "all" || paper.dataset.firstAuthor === "true";
    paper.hidden = !show;
    if (show) {
      count += 1;
      paper.querySelector(".paper-index").textContent = String(count).padStart(2, "0");
    }
  });
  filterButtons.forEach((button) => {
    button.setAttribute("aria-pressed", String(button.dataset.filter === mode));
  });
  if (announce) filterStatus.textContent = `Showing ${count} ${mode === "all" ? "papers" : "first-author papers, including equal contributions"}.`;
}

if (filterBar) {
  filterBar.hidden = false;
  filterButtons.forEach((button) => button.addEventListener("click", () => filterPapers(button.dataset.filter)));
  filterPapers("all", false);
}

const dialog = document.querySelector("#citation-dialog");
const citations = JSON.parse(document.querySelector("#citation-data").textContent);
const citationContent = document.querySelector("#citation-content");
const copyStatus = document.querySelector("#copy-status");

if (dialog && typeof dialog.showModal === "function") {
  document.querySelectorAll(".citation-link").forEach((anchor) => {
    anchor.addEventListener("click", (event) => {
      const citation = citations[anchor.dataset.citation];
      if (!citation) return;
      event.preventDefault();
      document.querySelector("#citation-paper").textContent = citation.title;
      citationContent.textContent = citation.bibtex;
      copyStatus.textContent = "";
      dialog.showModal();
    });
  });
  document.querySelector(".close-dialog").addEventListener("click", () => dialog.close());
  dialog.addEventListener("click", (event) => {
    const bounds = dialog.getBoundingClientRect();
    if (event.target === dialog && (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom)) dialog.close();
  });
  document.querySelector("#copy-citation").addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(citationContent.textContent);
      copyStatus.textContent = "Citation copied.";
    } catch {
      const range = document.createRange();
      range.selectNodeContents(citationContent);
      const selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
      copyStatus.textContent = "Citation selected. Press ⌘C or Ctrl+C to copy.";
    }
  });
}

// Reveal an individual paper even if it is outside the first-author view.
function revealLinkedPaper() {
  if (!location.hash.startsWith("#paper-")) return;
  const paper = document.getElementById(location.hash.slice(1));
  if (!paper) return;
  filterPapers("all", false);
  paper.scrollIntoView({ block: "start" });
}
window.addEventListener("hashchange", revealLinkedPaper);
revealLinkedPaper();
