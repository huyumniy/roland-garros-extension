export function filterZones(zones, {
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
