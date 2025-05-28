import { settings } from "../../models/settingsModel.js";
import { updateSettings } from "../../services/settingsStorage.js";

// Utility functions for managing selection states
/**
 * Removes the specified CSS class from all elements in the list.
 * @param {HTMLElement[]} elements - Array of elements to clear.
 * @param {string} className - CSS class to remove.
 */
function clearSelection(elements, className) {
  elements.forEach((element) => {
    element.classList.remove(className);
  });
}

/**
 * Ensures only one element in the list has the specified class.
 * @param {HTMLElement[]} elements - List of selectable elements.
 * @param {string} value - The data-value to match for selection.
 * @param {string} className - CSS class indicating selection.
 */
function selectSingleOption(elements, value, className) {
  clearSelection(elements, className);

  const match = elements.find((element) => element.dataset.value == value);

  if (match) {
    match.classList.add(className);
  }
}

function setDefaultSettings() {
  settings.amount = null;
  settings.date = "";
  settings.categories = [];
  settings.sessions = [];
  settings.courts = [];
  settings.minPrice = null;
  settings.maxPrice = null;
}

/**
 * Applies selection class to multiple elements based on matching values.
 * @param {HTMLElement[]} elements - List of selectable elements.
 * @param {string[]} values - Array of values (or text) to match.
 * @param {string} className - CSS class indicating selection.
 */
function selectMultipleOptions(elements, values, className) {
  clearSelection(elements, className);

  const normalizedValues = values.map((v) => v.trim().toLowerCase());

  elements.forEach((element) => {
    const text = element.textContent.trim().toLowerCase();
    if (normalizedValues.includes(text)) {
      element.classList.add(className);
    }
  });
}

export const UI = {
  __settingsHTML: "",
  __settingsCSS: "",

  /**
   * Initializes the settings UI: loads resources, injects HTML/CSS, binds events, and applies saved preferences.
   */
  async init() {
    // Load CSS and HTML templates
    const [cssText, htmlText] = await Promise.all([
      fetch(chrome.runtime.getURL("src/content-scripts/ui/settings.css")).then(
        (response) => response.text()
      ),
      fetch(chrome.runtime.getURL("src/content-scripts/ui/settings.html")).then(
        (response) => response.text()
      ),
    ]);

    this.__settingsCSS = cssText;
    this.__settingsHTML = htmlText;

    // Inject styles into document head
    const styleElement = document.createElement("style");
    styleElement.textContent = cssText;
    document.head.appendChild(styleElement);

    // Create and append settings container
    const container = document.createElement("div");
    container.id = "settingsFormContainer";
    container.innerHTML = htmlText;
    document.body.appendChild(container);

    // Query UI controls inside the container
    const ticketOptions = Array.from(
      container.querySelectorAll(".tickets_select .tickets_selector")
    );
    const dateOptions = Array.from(
      container.querySelectorAll(".date_select .tickets_selector")
    );
    const categoryOptions = Array.from(container.querySelectorAll(".selector"));
    const googleSheetsInput = container.querySelector('input[name="settings"]');

    // Bind click events for single-select (tickets and dates)
    ticketOptions.forEach((option) => {
      option.addEventListener("click", () => {
        selectSingleOption(
          ticketOptions,
          option.dataset.value,
          "tickets_selector_selected"
        );
      });
    });

    dateOptions.forEach((option) => {
      option.addEventListener("click", () => {
        selectSingleOption(
          dateOptions,
          option.dataset.value,
          "tickets_selector_selected"
        );
      });
    });

    // Bind click events for multi-select (categories)
    categoryOptions.forEach((option) => {
      option.addEventListener("click", () => {
        option.classList.toggle("selector_selected");
      });
    });

    container.querySelector('input[name="interval"]').value = settings.secondsToRestartIfNoTicketsFound || 15;
    let minimum_price = container.querySelector('input[name="minimum_price"]')
      minimum_price.value = settings.minPrice ?? '';
      let maximum_price = container.querySelector('input[name="maximum_price"]')
      maximum_price.value = settings.maxPrice ?? '';
    // Populate initial state based on saved settings
    if (settings.googleSheetsSettings) {
      // If Google Sheets is configured, clear other selections and settings
      setDefaultSettings();
      // Clear selections in UI
      googleSheetsInput.value = settings.googleSheetsSettings;
      clearSelection(ticketOptions, "tickets_selector_selected");
      clearSelection(dateOptions, "tickets_selector_selected");
      clearSelection(categoryOptions, "selector_selected");
      maximum_price.value = '';
      minimum_price.value = '';
    } else {
      // Use saved amount, date, and categories
      googleSheetsInput.value = settings.googleSheetsSettings || "";

      if (settings.amount) {
        selectSingleOption(
          ticketOptions,
          settings.amount,
          "tickets_selector_selected"
        );
      }

      if (settings.date) {
        selectSingleOption(
          dateOptions,
          settings.date,
          "tickets_selector_selected"
        );
      }

      if (settings.categories) {
        const combinedValues = [
          ...settings.categories,
          ...settings.sessions,
          ...settings.courts,
        ];

        selectMultipleOptions(
          categoryOptions,
          combinedValues,
          "selector_selected"
        );
      }
    }

    // Footer buttons: Cancel & Apply
    container
      .querySelector("#tickets_cancel")
      .addEventListener("click", this.closePopup.bind(this));
    container
      .querySelector("#tickets_start")
      .addEventListener("click", updateSettings);

    // Clicking outside popup content closes the modal
    const popupWrapper = container.querySelector(".tickets_popup_wrapper");
    popupWrapper.addEventListener("click", (event) => {
      if (event.target === popupWrapper) {
        this.closePopup();
      }
    });
  },

  /**
   * Shows the settings popup and prevents background scrolling.
   */
  openPopup() {
    const wrapper = document.querySelector(".tickets_popup_wrapper");
    wrapper.style.display = "block";
    document.body.style.overflow = "hidden";
  },

  /**
   * Hides the settings popup and restores background scrolling.
   */
  closePopup() {
    const wrapper = document.querySelector(".tickets_popup_wrapper");
    wrapper.style.display = "none";
    document.body.style.overflow = "auto";
  },

  /**
   * Creates initial button that used to open settings popup
   */
  createSettingsButton(onClick) {
    const btn = document.createElement("button");
    btn.textContent = "Налаштування";
    btn.className = "integrated-settings-button";
    Object.assign(btn.style, {
      position: "fixed",
      bottom: "15px",
      right: "15px",
      padding: "5px 10px",
      background: "#cc4e0e",
      color: "#fff",
      cursor: "pointer",
    });
    btn.addEventListener("click", onClick);
    document.body.appendChild(btn);
    return btn;
  },
};
