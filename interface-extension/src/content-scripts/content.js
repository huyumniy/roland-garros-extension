import { openDatabase } from "../services/db.js";
import { UI } from "./ui/settings.js";
import {
  dateToFullDateMapping,
  sessionMapping,
  courtMapping,
  sessionReverseMapping,
} from "../utils/mappings.mjs";
import { fetchSheetData } from "../services/googleSheets.js";
import { getData, sendData } from "../utils/fetchUtil.js";
import { saveSettings } from "../services/settingsStorage.js";
import { _countAndRun } from "../domain/scheduler.js";

import { filterDates } from "../domain/filters/dateFilter.js";
import { parseDateData } from "../domain/parsers/parseDateData.js";
import { filterZones } from "../domain/filters/zoneFilter.js";
import { parseZoneData } from "../domain/parsers/parseZoneData.js";
import { filterSeats } from "../domain/filters/seatFilter.js";
import { convertToPayload, findBiggestArray } from "../utils/helpers.js";

import { settings } from "../models/settingsModel.js";

const link = document.createElement("link");
link.rel = "stylesheet";
link.href = chrome.runtime.getURL("src/content-scripts/ui/settings.css");
document.head.appendChild(link);

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

export async function main() {
  console.log(settings);
  if (settings.stopExecutionFlag) {
    return;
  }

  const {
    entries,
    sessions,
    courts,
    dateParts,
    categories,
    minPrice,
    maxPrice,
  } = prepareFilterParams(settings);
  console.log(entries, dateParts);
  const ticketsLimit = 6;

  const {
    status: dateStatus,
    text: dateText,
    json: dateResponse,
    error: dateError,
  } = await getData(
    `https://tickets.rolandgarros.com/api/v2/en/ticket/calendar/offers-grouped-by-sorted-offer-type/${
      dateToFullDateMapping[dateParts[0]]
    }`
  );

  console.log("Date response:", dateResponse);
  if ((await captcha_check(dateResponse)) || dateStatus === 403) {
    console.log("Captcha detected, stopping execution.");
    settings.stopExecutionFlag = true;
    saveSettings();
    window.location.reload();
    return;
  }
  if (dateStatus !== 200 || !dateResponse || dateError) {
    console.error("Error fetching dates:", dateError, dateText);
    _countAndRun();
    return;
  }
  const dates = await filterDates(dateResponse, {
    entries,
    sessions,
    courts,
    dateParts,
    minPrice,
    maxPrice,
  });

  console.log("Filtered dates:", dates);

  if (!dates.length) {
    console.log("No suitable date found.");
    _countAndRun();
    return;
  }
  console.log(
    "FOUND DATES",
    dates,
    settings.advancedSettings?.length ? "advanced offers" : "simple offers"
  );
  const { offerId, sessionType, sessionId } = parseDateData(dates);

  const zoneLink = `https://tickets.rolandgarros.com/api/v2/en/ticket/category/page/offer/${offerId}/date/${
    dateToFullDateMapping[dateParts[0]]
  }/sessions/${sessionId}?nightSession=${sessionType === "night"}`;

  const {
    status: zoneStatus,
    text: zoneText,
    json: zoneResponse,
    error: zoneError,
  } = await getData(zoneLink);

  console.log("Zone response:", zoneResponse);

  if ((await captcha_check(zoneResponse)) || zoneStatus === 403) {
    console.log("Captcha detected, stopping execution.");
    settings.stopExecutionFlag = true;
    saveSettings();
    window.location.reload();
    return;
  }

  if (!zoneResponse || zoneStatus !== 200 || zoneError) {
    console.error("Error fetching zones:", zoneError, zoneText);
    _countAndRun();
    return;
  }

  const { zoneOffer, filteredZones, categoryDefinitionById } = filterZones(
    zoneResponse,
    {
      entries,
      categories,
      minPrice,
      maxPrice,
    }
  );
  console.log("Filtered zones:", filteredZones);
  if (!filteredZones.length) {
    console.log("No suitable zones found.");
    _countAndRun();
    return;
  }
  console.log(
    "Successfully filtered zones and mappings:",
    filteredZones,
    categoryDefinitionById
  );

  const { zoneId, priceId, categoryName } = parseZoneData(
    filteredZones,
    categoryDefinitionById
  );

  const seatsLink = `https://tickets.rolandgarros.com/api/v2/ticket/category/zone/${zoneId}/sessions/${sessionId}/priceId/${priceId}?nightSession=${
    sessionType === "night"
  }`;

  console.log("Seats link:", seatsLink);

  const {
    status: seatsStatus,
    text: seatsText,
    json: seatsResponse,
    error: seatsError,
  } = await getData(seatsLink);

  console.log("Seats response:", seatsResponse);
  if ((await captcha_check(seatsResponse)) || seatsStatus === 403) {
    console.log("Captcha detected, stopping execution.");
    settings.stopExecutionFlag = true;
    saveSettings();
    window.location.reload();
    return;
  }
  if (!seatsResponse || seatsStatus !== 200 || seatsError) {
    console.error("Error fetching seats:", seatsError, seatsText);
    _countAndRun();
    return;
  }
  const desiredAmount = settings.advancedSettings
    ? getCategoryAmount(entries, {
        date: dateParts[0],
        court: courtMapping[zoneOffer.court],
        session: sessionMapping[zoneOffer.sessionTypes],
        category: categoryName,
      })
    : settings.amount
    ? settings.amount
    : 1;
  const filteredSeats = filterSeats(seatsResponse, desiredAmount);

  console.log("Filtered seats:", filteredSeats);
  if (!filteredSeats.length) {
    console.log("No suitable seats found.");
    _countAndRun();
    return;
  }
  // console.log("Successfully filtered seats:", filteredSeats);
  const biggestArrayOfSeats = findBiggestArray(filteredSeats);

  const arrayOfPayloads = convertToPayload(biggestArrayOfSeats, priceId);

  if (!arrayOfPayloads.length) {
    console.log("No payloads to send.");
    _countAndRun();
    return;
  }
  console.log("Successfully converted to payload:", arrayOfPayloads);
  const purchaseLink = `https://tickets.rolandgarros.com/api/v2/ticket/cart/ticket-product-by-seat`;

  const ajaxPurchaseLink = `https://tickets.rolandgarros.com/en/ticket/categorie?date=${
    dateToFullDateMapping[dateParts[0]]
  }&offerId=${offerId}&sessionIds=${sessionId}&sessionTypes=${
    sessionReverseMapping[sessionType]
  }&court=${zoneOffer.court}&dateDescription=${
    zoneOffer.sessionDatesLabel
  }&offerType=SINGLE_DAY`;

  const options = {
    headers: {
      "Content-Type": "application/json",
      "x-queueit-ajaxpageurl": encodeURIComponent(ajaxPurchaseLink),
    },
  };
  let boughtTickets = 0;
  for (const payload of arrayOfPayloads) {
    if (boughtTickets >= ticketsLimit) {
      console.log("Reached the limit of bought tickets:", ticketsLimit);
      break;
    }
    const {
      status: purchaseStatus,
      text: purchaseText,
      json: purchaseResponse,
      error: purchaseError,
    } = await sendData(purchaseLink, payload, options);

    if ((await captcha_check(purchaseResponse)) || purchaseStatus === 403) {
      console.log("Captcha detected, stopping execution.");
      settings.stopExecutionFlag = true;
      saveSettings();
      window.location.reload();
      return;
    }
    if (!purchaseResponse || purchaseStatus !== 200 || purchaseError) {
      console.error(
        "Error sending purchase request:",
        purchaseError,
        purchaseText
      );
      // displayTextInBottomLeftCorner(purchaseText || purchaseError || "Unknown error");
      _countAndRun();
      return;
    }
    if (purchaseResponse.seatDetails && purchaseResponse.seatDetails.length) {
      boughtTickets += purchaseResponse.seatDetails.length;
      console.log(
        "Successfully bought tickets:",
        purchaseResponse.seatDetails.length
      );
    }
  }
  if (boughtTickets === 0) {
    console.log("No tickets were bought, something went wrong.");
    _countAndRun();
    return;
  }

  console.log("Finished execution, bought tickets:", boughtTickets);
  alert(
    `Successfully bought ${boughtTickets} tickets! Please check your cart.`
  );
  stopExecutionFlag = true;
  return;
}

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
      categories: [],
      minPrice,
      maxPrice,
    };
  }

  const datePart = settings.date || null;
  return {
    entries: [],
    sessions: settings.sessions || [],
    courts: settings.courts || [],
    dateParts: datePart ? [datePart] : [],
    categories: settings.categories || [],
    minPrice,
    maxPrice,
  };
}

function getCategoryAmount(entries, { date, court, session, category }) {
  const entry = entries.find(
    (item) =>
      item.date === date && item.court === court && item.session === session
  );
  if (!entry) return 0;

  const catObj = entry.categories.find((obj) =>
    Object.prototype.hasOwnProperty.call(obj, category)
  );
  if (!catObj) return 0;

  return catObj[category] || 0;
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
