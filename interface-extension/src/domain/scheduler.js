import { settings } from "../models/settingsModel.js";
import { main } from "../content-scripts/content.js";

export function _countAndRun() {
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

export function _countScriptRunning() {
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