"use strict";

// All papers are rendered in profile order. JavaScript only enhances citations.
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
