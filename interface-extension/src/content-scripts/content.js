import { openDatabase } from "../services/db.js";
import { UI } from "./ui/settings.js";
import {
  dateToFullDateMapping,
  sessionMapping,
  courtMapping,
} from "../utils/mappings.mjs";
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

async function captcha_check(data) {
  if (data?.url && data.url.includes("geo.captcha-delivery.com/captcha")) {
    await send_slack_message();
    return true;
  } else return false;
}

async function main() {
  const { entries, sessions, courts, dateParts, minPrice, maxPrice } =
    prepareFilterParams(settings);
  console.log(entries, dateParts);
  const dateResponse = await fetchData(
    `https://tickets.rolandgarros.com/api/v2/en/ticket/calendar/offers-grouped-by-sorted-offer-type/${
      dateToFullDateMapping[dateParts[0]]
    }`
  );
  if (!dateResponse || (await captcha_check(dateResponse))) {
    console.log("No suitable date found.");
    _countAndRun();
    return;
  }
  const offers = await filterDates(dateResponse, {
    entries,
    sessions,
    courts,
    dateParts,
    minPrice,
    maxPrice,
  });

  if (!offers.length) {
    console.log("No tickets found.");
  } else {
    console.log(
      "Successfuly found necessary tickets!!!",
      offers,
      settings.advancedSettings?.length ? "advanced offers" : "simple offers"
    );
  }
}
/**
 * Prepares filtering parameters based on settings mode.
 * For advancedSettings: picks a random date group and its entries.
 * For simple mode: extracts datePart, sessions, and courts arrays.
 */
function prepareFilterParams(settings) {
  const minPrice = settings.minPrice ?? 0;
  const maxPrice = settings.maxPrice ?? Infinity;

  if (settings.advancedSettings?.length) {
    const groups = settings.advancedSettings;
    const uniqueDates = [...new Set(groups.map((d) => d.date))];

    const randomDate =
      uniqueDates[Math.floor(Math.random() * uniqueDates.length)];
    const entries = groups.filter((d) => d.date === randomDate);

    return {
      entries,
      sessions: [],
      courts: [],
      dateParts: [randomDate],
      minPrice,
      maxPrice,
    };
  }

  const datePart = settings.date?.split(" ").slice(1).join(" ") || null;
  return {
    entries: [],
    sessions: settings.sessions || [],
    courts: settings.courts || [],
    dateParts: datePart ? [datePart] : [],
    minPrice,
    maxPrice,
  };
}

/**
 * Generic offer filtering:
 * - SINGLE_DAY & available overall
 * - isAvailable && price range
 * - optional advanced entries (session+court+date)
 * - optional simple sessions/courts + dateParts
 */
function filterDates({
  entries,
  sessions = [],
  courts = [],
  dateParts = [],
  minPrice,
  maxPrice,
}) {
  return date
    .filter(
      (e) => e.offerType.offerType === "SINGLE_DAY" && e.isOfferTypeAvailable
    )
    .flatMap((e) => e.offers)
    .filter((offer) => {
      if (!offer.isAvailable) return false;

      if (
        minPrice !== undefined &&
        offer.minPrice <= minPrice &&
        maxPrice !== undefined &&
        offer.minPrice >= maxPrice
      )
        return false;

      const mappedSession = sessionMapping[offer.sessionTypes];
      const mappedCourt = courtMapping[offer.court];

      // advancedSettings mode:

      if (Array.isArray(entries) && entries.length) {
        return entries.some((d) => {
          if (d.session !== mappedSession || d.court !== mappedCourt)
            return false;
          const part = d.date.split(" ").slice(1).join(" ");
          return hasDateMatch(offer, part);
        });
      } else {
        // simple mode:
        if (sessions.length && !sessions.includes(mappedSession)) return false;
        if (courts.length && !courts.includes(mappedCourt)) return false;
        if (dateParts.length && !dateParts.some((p) => hasDateMatch(offer, p)))
          return false;
      }

      return true;
    });
}
/**
 * Checks if offer has any session matching "DD MONTH" string
 */
function hasDateMatch(offer, datePart) {
  return offer.sessions.some((s) => {
    const [, dayNum, monthWord] = s.dateLongDescription.split(" ");
    return `${dayNum} ${monthWord.toUpperCase()}` === datePart;
  });
}

function displayTextInBottomLeftCorner(text) {
  const existingTextElement = document.getElementById("bottomLeftText");

  function formatNumber(num) {
    return num < 10 ? `0${num}` : num;
  }

  function getCurrentTime() {
    const now = new Date();
    const hours = formatNumber(now.getHours());
    const minutes = formatNumber(now.getMinutes());
    const seconds = formatNumber(now.getSeconds());
    return `${hours}:${minutes}:${seconds}`;
  }

  if (!existingTextElement) {
    const newTextElement = document.createElement("div");
    newTextElement.id = "bottomLeftText";
    newTextElement.style.display = "block";
    newTextElement.style.padding = "10px";
    newTextElement.style.backgroundColor = "#000";
    newTextElement.style.color = "#fff";
    newTextElement.style.fontFamily = "Arial, sans-serif";

    let bottomLeftInfo = document.getElementById("bottomLeftContainer");
    if (bottomLeftInfo) {
      bottomLeftInfo.appendChild(newTextElement);
    } else {
      let bottomLeftInfo = document.createElement("div");
      bottomLeftInfo.id = "bottomLeftContainer";
      bottomLeftInfo.style.display = "flex";
      bottomLeftInfo.style.gap = "5px";
      bottomLeftInfo.style.flexDirection = "column";
      bottomLeftInfo.style.position = "absolute";
      bottomLeftInfo.style.maxWidth = "50%";
      bottomLeftInfo.style.bottom = "0";
      bottomLeftInfo.style.left = "0";
      document.body.appendChild(bottomLeftInfo);
      bottomLeftInfo.appendChild(newTextElement);
    }

    newTextElement.textContent = `${text} - ${getCurrentTime()}`;
  } else {
    existingTextElement.textContent = `${text} - ${getCurrentTime()}`;
  }
}

function _countAndRun() {
  // displayTextInBottomLeftCorner("No tickets found!");
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
