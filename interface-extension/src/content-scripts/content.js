import { openDatabase } from "../services/db.js";
import { UI } from "./ui/settings.js";
import { fetchSheetData } from "../services/googleSheets.js";

const link = document.createElement("link");
link.rel = "stylesheet";
link.href = chrome.runtime.getURL("src/content-scripts/ui/settings.css");
document.head.appendChild(link);

export let settings = {
  amount: null,
  date: null,
  categories: [],
  sessions: [],
  courts: [],
  googleSheetsSettings: false,
  timesToBrowserTabReload: 200,
  secondsToRestartIfNoTicketsFound: 10,
  stopExecutionFlag: true,
  advancedSettings: [],
};

(async function init() {
  const db = await openDatabase();
  const tx = db.transaction("settings", "readwrite");
  const store = tx.objectStore("settings");
  const req = store.get(1);
  req.onsuccess = (e) => {
    const result = e.target.result;
    if (result) settings = result.settings;
    setupUI();
  };
  req.onerror = () => setupUI();
})();

async function setupUI() {
  await UI.init();
  UI.createSettingsButton(UI.openPopup);
  mainLoop();
}

async function mainLoop() {
  // main reservation/checking logic using settings
  console.log("Starting main()");
}

async function updateGoogleSheetSettings() {
  console.log("Updating Google Sheets settings...");
  if (settings.googleSheetsSettings) {
    settings.advancedSettings = await fetchSheetData(
      settings.googleSheetsSettings
    );
    console.log(settings.advancedSettings);
  }
}

setInterval(() => {
  updateGoogleSheetSettings().catch(console.error);
}, 60_000);
// (async () => receive_sheets_data_main())();
