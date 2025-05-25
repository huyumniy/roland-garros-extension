import { settings } from "../utils/advancedSettings.mjs";
import { dateToFullDateMapping, sessionMapping } from "../utils/mappings.mjs";
import { date } from "../utils/date.mjs";

async function main() {
  const minPrice = 0;
  const maxPrice = 110;

  const filteredUniqueDates = filterByUniqueDates(settings.advancedSettings);
  const randomFilteredUniqueDate =
    filteredUniqueDates[Math.floor(Math.random() * filteredUniqueDates.length)];

  const desiredDates = settings.date
    ? [settings.date]
    : filterByDate(settings.advancedSettings, randomFilteredUniqueDate.date);

  const processDateData = await processDate(
    settings,
    desiredDates,
    minPrice,
    maxPrice
  );
  if (!processDateData.length) {
    console.log("No tickets found.");
    // _countAndRun();
    return;
  }

  // console.log(processDateData);s
}

async function processDate(settings, dates, minPrice, maxPrice) {
  console.log("processDate");

  if (!dates.length) {
    return [];
  }

  // const dateResponse = await fetchData(
  //   `https://tickets.rolandgarros.com/api/v2/en/ticket/calendar/offers-grouped-by-sorted-offer-type/${dateToFullDateMapping[dates[0].date]}`
  // );
  const dateResponse = date;
  if (!dateResponse || dateResponse?.url) {
    return [];
  }

  const offers = dateResponse
    .filter(
      (offer) =>
        offer.offerType.offerType === "SINGLE_DAY" && offer.isOfferTypeAvailable
    )
    .map((offer) => {
      return offer.offers;
    });

  

  offers.filter(
    (offer) => offer.isAvailable 
    && dates.includes({'session': sessionMapping[offer.sessionTypes]})
    && 
  );

  return offers;
}

// |------------------------------------|
// |               Utils                |
// |------------------------------------|

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

/**
 * @param {Array<Object>} data  – your full list of schedule objects
 * @param {string}        date  – the exact date label to filter by (e.g. "SUN 1 JUNE")
 * @returns {Array<Object>}     – all objects whose `date` equals the given string
 */
function filterByDate(data, date) {
  return data.filter((item) => item.date === date);
}

main();
