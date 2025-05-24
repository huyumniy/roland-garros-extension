import {
  dateMapping,
  sessionMapping,
  courtMapping,
} from "../utils/mappings.js";

export async function fetchSheetData(sheetUrl) {
  const SHEET_ID = sheetUrl.split("/d/")[1].split("/")[0];
  const SHEET_TITLE = "main";
  const SHEET_RANGE = "A2:H";
  const FULL_URL = `https://docs.google.com/spreadsheets/d/${SHEET_ID}/gviz/tq?sheet=${SHEET_TITLE}&range=${SHEET_RANGE}`;

  try {
    const text = await fetch(FULL_URL).then((res) => res.text());
    const {
      table: { rows },
    } = JSON.parse(text.slice(47, -2));
    
    const result = rows
        .map(({ c }) => {
          const categories = [
            ["category 3", c[2]?.v],
            ["category 2", c[3]?.v],
            ["category 1", c[4]?.v],
            ["category gold", c[5]?.v],
            ["box", c[6]?.v],
          ]
            .filter(([name, val]) => val != null && val !== "")
            .map(([name, val]) => ({ [name]: val }));
          return {
            date: dateMapping[isNaN(c[0]?.v) ? parseInt(c[0]?.v) : c[0]?.v],
            court: courtMapping[c[1]?.v],
            session: sessionMapping[c[1]?.v],
            categories,
          };
        })
        .filter((item) => item.date && item.categories.length > 0);
      return result;
  } catch (error) {
    console.error("Error fetching sheet data:", error);
    return [];
  }
}
