import { openDatabase } from "../services/db.js";
import { UI } from "./ui/settings.js";
import { fetchSheetData } from "../services/googleSheets.js";
import { fetchData } from "../utils/fetch_util.js";

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
  timesToBrowserTabReload: 200,
  secondsToRestartIfNoTicketsFound: 15,
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
  main();
}

async function main() {
  // main reservation/checking logic using settings
  console.log("Starting main()");
  const filteredUniqueDates = filterByUniqueDates(advancedSettings);
  const randomFilteredUniqueDate =
    filteredUniqueDates[Math.floor(Math.random() * filteredUniqueDates.length)];

  const desiredDate = settings.date
    ? settings.date
    : randomFilteredUniqueDate.date;

  // const dateResponse = await fetchData(
  //   `https://tickets.rolandgarros.com/api/v2/en/ticket/calendar/offers-grouped-by-sorted-offer-type/`
  // );
}

/**
 * Filters an array of schedule objects so that only the first object
 * for each unique `date` remains.
 *
 * @param {Array<Object>} data – array of dates and its properties
 * @returns {Array<Object>} filtered list with unique only dates
 */
function filterByUniqueDates(data) {
  const seenDates = new Set();
  return data.filter((item) => {
    if (seenDates.has(item.date)) {
      return false;
    }
    seenDates.add(item.date);
    return true;
  });
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

function _countAndRun() {
  displayTextInBottomLeftCorner("No tickets found!");
  console.log("No tickets found!");
  setTimeout(
    () => {
      _countScriptRunning();
      main();
      console.log("calling main function");
    },
    settings.secondsToRestartIfNoTicketsFound
      ? settings.secondsToRestartIfNoTicketsFound * 1000
      : 5 * 1000
  );
}

function _countScriptRunning() {
  let ticketCatcherCounter = sessionStorage.getItem("RealTicketCatcherCounter");
  if (ticketCatcherCounter === null) ticketCatcherCounter = 1;
  console.log(
    'Script "' +
      '" has been run ' +
      ticketCatcherCounter +
      " times from " +
      settings.timesToBrowserTabReload +
      "."
  );
  if (ticketCatcherCounter >= settings.timesToBrowserTabReload) {
    sessionStorage.setItem("RealTicketCatcherCounter", 0);
    console.log("reloading page...");
    window.location.reload();
  } else {
    sessionStorage.setItem("RealTicketCatcherCounter", ++ticketCatcherCounter);
  }
}

setInterval(() => {
  updateGoogleSheetSettings().catch(console.error);
}, 60_000);
// (async () => receive_sheets_data_main())();
