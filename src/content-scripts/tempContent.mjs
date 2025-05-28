import { settings } from "../test-fixtures/advancedSettingsDate.mjs";
import {
  dateToFullDateMapping,
  sessionMapping,
  courtMapping,
} from "../utils/mappings.mjs";
import { date } from "../test-fixtures/date.mjs";
import { zones } from "../test-fixtures/zone.mjs";
import { seats } from "../test-fixtures/seat.mjs";
import { bookResponse } from "../test-fixtures/bookResponse.mjs";

async function main() {
  const { entries, sessions, courts, dateParts, categories, minPrice, maxPrice } =
    prepareFilterParams(settings);
  console.log(dateParts);
  const ticketsLimit = 6;
  const dates = filterDates(date, {
    entries,
    sessions,
    courts,
    dateParts,
    minPrice,
    maxPrice,
  });

  if (!dates.length) {
    console.log("No active date found.");
    // _countAndRun();
    return;
  }

  // console.log(
  //   "Successfuly found necessary tickets!!!",
  //   offers,
  //   settings.advancedSettings?.length ? "advanced offers" : "simple offers"
  // );

  const {offerId, sessionType, sessionId} = parseDateData(dates);
  // console.log("Parsed date data:", { offerId, sessionType, sessionId });
  
  const zoneLink = `https://tickets.rolandgarros.com/api/v2/en/ticket/category/page/offer/${offerId}/date/${dateToFullDateMapping[dateParts[0]]}/sessions/${sessionId}?nightSession=${sessionType === "night"}`;

  // const zoneResponse = await fetchData(zoneLink);
  //   console.log("Date response:", zoneResponse);
  //   if (!zoneResponse) {
  //     console.log("No suitable zones found.");
  //     _countAndRun();
  //     return;
  //   }
  //   if (await captcha_check(zoneResponse)) {
  //     console.log("Captcha detected, stopping execution.");
  //     settings.stopExecutionFlag = true;
  //   }
  const {zoneOffer, filteredZones, categoryDefinitionById } = filterZones(zones, {
    entries, categories, minPrice, maxPrice
  })
  // console.log("Filtered zones:", filteredZones);
  if (!filteredZones.length) {
    console.log("No suitable zones found.");
    // _countAndRun();
    return;
  }
  // console.log("Successfully filtered zones and mappings:", filteredZones, categoryDefinitionById);
  
  const { zoneId, priceId, categoryName } = parseZoneData(filteredZones, categoryDefinitionById)

  const seatsLink = `/api/v2/ticket/category/zone/${zoneId}/sessions/${sessionId}/priceId/${priceId}?nightSession=${sessionType === "night"}`

  // console.log("Seats link:", seatsLink);

  // const seatsResponse = await fetchData(seatsLink);
  // console.log("Seats response:", seatsResponse);
  // if (!seatsResponse) {
  //   console.log("No seats response found.");
  //   _countAndRun();
  //   return;
  // }
  // if (await captcha_check(seatsResponse)) {
  //   console.log("Captcha detected, stopping execution.");
  //   settings.stopExecutionFlag = true;
  //   return;
  // }
  const desiredAmount = settings.advancedSettings ? getCategoryAmount(entries, {
    date: dateParts[0],
    court: courtMapping[zoneOffer.court],
    session: sessionMapping[zoneOffer.sessionTypes],
    category: categoryName,
  }) : settings.amount ? settings.amount : 1;
  const filteredSeats = filterSeats(seats, desiredAmount)
  console.log("Filtered seats:", filteredSeats);
  if (!filteredSeats.length) {
    console.log("No suitable seats found.");
    // _countAndRun();
    return;
  }
  // console.log("Successfully filtered seats:", filteredSeats);
  const biggestArrayOfSeats = findBiggestArray(filteredSeats)

  const arrayOfPayloads = convertToPayload(biggestArrayOfSeats, priceId)

  if (!arrayOfPayloads.length) {
    console.log("No payloads to send.");
    // _countAndRun();
    return;
  }
  console.log("Successfully converted to payload:", arrayOfPayloads);
  const purchaseLink = `/api/v2/ticket/cart/ticket-product-by-seat`;


  let boughtTickets = 0;
  for (const payload of arrayOfPayloads) {
    if (boughtTickets >= ticketsLimit) {
      console.log("Reached the limit of bought tickets:", ticketsLimit);
      break;
    }
    // const purchaseResponse = await postData(purchaseLink, payload);
    const purchaseResponse = bookResponse;
    if (!purchaseResponse) {
      console.log("Did not receive a response from the purchase request.");
      // _countAndRun();
      return;
    }
    // if (await captcha_check(purchaseResponse)) {
    //   console.log("Captcha detected, stopping execution.");
    //   settings.stopExecutionFlag = true;
    // }
    if (purchaseResponse.tickets && purchaseResponse.tickets.length) {
      boughtTickets = purchaseResponse.tickets.length;
      console.log("Successfully bought tickets:", purchaseResponse.tickets.length);
    } 
  }
  if (boughtTickets === 0) {
    console.log("No tickets were bought, something went wrong.");
  }
  // _countAndRun();
  console.log("Finished execution, bought tickets:", boughtTickets);
  
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

/**
 * Generic offer filtering:
 * - SINGLE_DAY & available overall
 * - isAvailable && price range
 * - optional advanced entries (session+court+date)
 * - optional simple sessions/courts + dateParts
 */
function filterDates(dates, {
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
  console.log("checking date match for:", datePart);
  return offer.sessions.some((s) => {
    const [, dayNum, monthWord] = s.dateLongDescription.split(" ");
    console.log("Checking date match:", `${dayNum} ${monthWord.toUpperCase()}`, datePart.split(" ").slice(1).join(" ").toUpperCase(), `${dayNum} ${monthWord.toUpperCase()}` === datePart.split(" ").slice(1).join(" ").toUpperCase());
    return `${dayNum} ${monthWord.toUpperCase()}` === datePart.split(" ").slice(1).join(" ").toUpperCase();
  });
}

function parseDateData(dates) {
  if (!dates.length) {
    console.log("No offers to parse date data from.");
    return {};
  }

  const date = dates[0];
  const sessionType = sessionMapping[date.sessionTypes];
  const sessionId = date.sessionIds[0];

  return {
    offerId: date.offerId,
    sessionType,
    sessionId,
  };
}

function filterZones(zones, {
  entries = [],
  categories = [],
  minPrice,
  maxPrice,
  requiredTicketCount = 1
}) {
  console.log("Filtering zones with parameters:", {
    entries,
    categories,
    minPrice,
    maxPrice,
    requiredTicketCount
  });

  const zoneOffer = zones.offer;
  // Build list of category definitions with known prices
  const categoryDefinitions = zones.categories.filter(def => def.price != null);

  // Map category names (lowercased) to their IDs
  const categoryNameToIdMap = {};
  categoryDefinitions.forEach(({ id, longName, shortName, code }) => {
    [longName, shortName, code].forEach(name => {
      if (name) categoryNameToIdMap[name.toLowerCase()] = id;
    });
  });

  // Map category ID to its full definition for quick lookups
  const categoryDefinitionById = Object.fromEntries(
    categoryDefinitions.map(def => [def.id, def])
  );


  // Helper: return all stadium zones that have at least `count` tickets for `categoryId`
  function getZonesWithStock(categoryId, count) {
    return zones.stadium.zoneCoordinates.filter(zone => {
      const stockEntry = zone.categoryZoneStocks.find(s => s.categoryId === categoryId);
      return stockEntry && stockEntry.quantity >= count;
    });
  }

  let filteredZones;

  // ADVANCED MODE
  if (entries.length) {
    const matchingZoneIds = new Set();

    entries.forEach(requirementEntry => {
      requirementEntry.categories.forEach(categoryCountObj => {
        const [categoryName, count] = Object.entries(categoryCountObj)[0];
        const categoryId = categoryNameToIdMap[categoryName.toLowerCase()];
        if (!categoryId) return;

        const zonesMeeting = getZonesWithStock(categoryId, count);
        zonesMeeting.forEach(zone => matchingZoneIds.add(zone.id));
      });
    });

    filteredZones = Array.from(matchingZoneIds).map(id =>
      zones.stadium.zoneCoordinates.find(zone => zone.id === id)
    );
  } else {
    // SIMPLE MODE
    const desiredCategoryIds = categories.length
      ? categories
          .map(name => categoryNameToIdMap[name.toLowerCase()])
          .filter(Boolean)
      : categoryDefinitions.map(def => def.id);

    filteredZones = zones.stadium.zoneCoordinates.filter(zone => {
      const availableStocks = zone.categoryZoneStocks.filter(stock =>
        desiredCategoryIds.includes(stock.categoryId) && stock.quantity > 0
      );
      if (!availableStocks.length) return false;

      const totalAvailable = availableStocks.reduce((sum, stock) => sum + stock.quantity, 0);
      if (totalAvailable < requiredTicketCount) return false;

      if (minPrice != null || maxPrice != null) {
        const withinPrice = availableStocks.some(stock => {
          const price = categoryDefinitionById[stock.categoryId].price;
          const aboveMin = minPrice == null || price >= minPrice;
          const belowMax = maxPrice == null || price <= maxPrice;
          return aboveMin && belowMax;
        });
        if (!withinPrice) return false;
      }

      return true;
    });
  }

  // Return both filtered zones and the category definition map
  return {
    zoneOffer,
    filteredZones,
    categoryDefinitionById
  };
}

function parseZoneData(zones, categoryDefinitionById) {
  if (!zones.length) {
    console.log("No zones to parse from.");
    return {};
  }

  const randomZone = zones[Math.floor(Math.random() * zones.length)];

  const zoneId = randomZone.id;
  const categoryStock = randomZone.categoryZoneStocks[0];
  const categoryDefinition = categoryStock ? categoryStock.categoryId : null;
  if (!categoryDefinition) {
    console.log("No price ID found in the selected zone.");
    return {};
  }
  const priceId = categoryDefinitionById[categoryDefinition].priceId;
  const categoryName = categoryDefinitionById[categoryDefinition].longName;

  return { zoneId, priceId, categoryName}
}

function filterSeats(array, quantity) {
  const nums = array.seatCoordinates
    .filter(s => s.isAvailable && !s.isInCart)
    .map(s => parseInt(s.id, 10))
    .sort((a, b) => a - b);

  if (nums.length === 0) {
    return [];
  }

  const results = [];
  let currentChain = [ nums[0] ];

  for (let i = 1; i < nums.length; i++) {
    const diff = nums[i] - nums[i - 1];
    if (diff === 1 || diff === 2) {
      currentChain.push(nums[i]);
    } else {
      if (currentChain.length >= quantity) {
        results.push(currentChain.map(String));
      }
      currentChain = [ nums[i] ];
    }
  }

  if (currentChain.length >= quantity) {
    results.push(currentChain.map(String));
  }

  return results;
}


/**
 * Look up how many seats of a given category were requested
 * for a particular date/court/session in your advancedSettings.
 *
 * @param {typeof entries} entries - the advancedSettings array
 * @param {{date: string, court: string, session: string, category: string}} props
 * @returns {number}  the requested amount, or 0 if not found
 */
function getCategoryAmount(entries, { date, court, session, category }) {
  // find the matching advancedSettings entry
  const entry = entries.find(item =>
    item.date    === date &&
    item.court   === court &&
    item.session === session
  );
  if (!entry) return 0;

  // look for the category object that has our key
  const catObj = entry.categories.find(obj =>
    Object.prototype.hasOwnProperty.call(obj, category)
  );
  if (!catObj) return 0;

  return catObj[category] || 0;
}

const findBiggestArray = arr => arr.reduce((a, b) => b.length > a.length ? b : a, []);

const convertToPayload = (arr, priceId) => {
  return arr.map(seat => ({
    seatId: seat,
    priceId: priceId,
  }));
  
}


main();
