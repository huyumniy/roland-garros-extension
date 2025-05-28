export function parseZoneData(zones, categoryDefinitionById) {
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
