import { settings } from "../utils/advancedSettingsDate.mjs";
import {
  dateToFullDateMapping,
  sessionMapping,
  courtMapping,
} from "../utils/mappings.mjs";
import { date } from "../utils/date.mjs";

async function main() {
  const { entries, sessions, courts, dateParts, minPrice, maxPrice } =
    prepareFilterParams(settings);
  console.log(dateParts);
  const offers = filterDates({
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

main();
