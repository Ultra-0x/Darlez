document.addEventListener("click", function (event) {
  const toggle = event.target.closest("[data-password-toggle]");
  if (!toggle) {
    return;
  }

  const input = document.getElementById(toggle.dataset.passwordTarget);
  if (!input || (input.type !== "password" && input.type !== "text")) {
    return;
  }

  const isVisible = input.type === "password";
  input.type = isVisible ? "text" : "password";
  toggle.setAttribute("aria-pressed", String(isVisible));
  toggle.setAttribute("aria-label", isVisible ? "Hide password" : "Show password");
  toggle.setAttribute("title", isVisible ? "Hide password" : "Show password");

  const icon = toggle.querySelector("[data-password-toggle-icon]");
  if (icon) {
    icon.classList.toggle("bi-eye", !isVisible);
    icon.classList.toggle("bi-eye-slash", isVisible);
  }
});
