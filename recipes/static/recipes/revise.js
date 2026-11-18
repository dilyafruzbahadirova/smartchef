"use strict";
document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("sc-proposal-form");
  const button = document.getElementById("sc-proposal-button");
  const wait = document.getElementById("sc-proposal-wait");
  if (!form || !button || !wait) return;
  form.addEventListener("submit", event => {
    const input = document.getElementById("sc-instruction");
    const value = input.value.trim();
    if (value.length < 3 || value.length > 300) {
      event.preventDefault();
      input.setCustomValidity(input.dataset.error || "3–300");
      input.reportValidity();
      return;
    }
    input.setCustomValidity("");
    button.disabled = true;
    wait.hidden = false;
  });
  document.getElementById("sc-instruction").addEventListener("input", e => e.target.setCustomValidity(""));
});
