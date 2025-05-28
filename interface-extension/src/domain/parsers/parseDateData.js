import { sessionMapping } from "../../utils/mappings.mjs";
export function parseDateData(dates) {
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
