import { sessionMapping, courtMapping } from "../../utils/mappings.mjs";
/**
 * Generic offer filtering:
 * - SINGLE_DAY & available overall
 * - isAvailable && price range
 * - optional advanced entries (session+court+date)
 * - optional simple sessions/courts + dateParts
 */
export function filterDates(dates, {
  entries,
  sessions = [],
  courts = [],
  dateParts = [],
  minPrice,
  maxPrice,
}) {
  return dates
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
          const part = d.date
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
    return `${dayNum} ${monthWord.toUpperCase()}` === datePart.split(" ").slice(1).join(" ").toUpperCase();
  });
}
