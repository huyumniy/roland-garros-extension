window.onload = () => {
  let db;
  let settings = {
    amount: null,
    date: null,
    categories: [],
    sessions: [],
    courts: [],
    googleSheetsSettings: false,
    timesToBrowserTabReload: 200,
    secondsToRestartIfNoTicketsFound: 10,
    stopExecutionFlag: true,
  };

  let UI = {
    __settingsHTML: `<div class="tickets tickets_popup_wrapper">
    <div class="tickets tickets_popup">
      <h1 class="tickets tickets_h1">Налаштування</h1>

      <h2 class="tickets tickets_h2">Квитки</h2>
      <span class="tickets tickets_title">Кількість:</span>
      <div class="tickets_select" data-select="count">
        <div class="tickets tickets_selector" data-value="1">1</div>
        <div class="tickets tickets_selector" data-value="2">2</div>
        <div class="tickets tickets_selector" data-value="3">3</div>
        <div class="tickets tickets_selector" data-value="4">4</div>
        <div class="tickets tickets_selector" data-value="5">5</div>
        <div class="tickets tickets_selector tickets_selector_selected" data-value="6">6</div>
      </div>

      <br>

      <span class="tickets tickets_title">Дати:</span>
      <div class="date_select" data-select="count">
        <div class="tickets tickets_selector" data-value="MON 19 MAY">19</div>
        <div class="tickets tickets_selector" data-value="TUE 20 MAY">20</div>
        <div class="tickets tickets_selector" data-value="WED 21 MAY">21</div>
        <div class="tickets tickets_selector" data-value="THU 22 MAY">22</div>
        <div class="tickets tickets_selector" data-value="FRI 23 MAY">23</div>
        <div class="tickets tickets_selector tickets_selector_selected" data-value="SAT 24 MAY">24</div>
        <div class="tickets tickets_selector" data-value="SAT 25 MAY">25</div>
        <div class="tickets tickets_selector" data-value="MON 26 MAY">26</div>
        <div class="tickets tickets_selector" data-value="TUE 27 MAY">27</div>
        <div class="tickets tickets_selector" data-value="WED 28 MAY">28</div>
        <div class="tickets tickets_selector" data-value="THU 29 MAY">29</div>
        <div class="tickets tickets_selector" data-value="FRI 30 MAY">30</div>
        <div class="tickets tickets_selector" data-value="SAT 31 MAY">31</div>
        <div class="tickets tickets_selector" data-value="SUN 1 JUNE">01</div>
        <div class="tickets tickets_selector" data-value="MON 2 JUNE">02</div>
        <div class="tickets tickets_selector" data-value="TUE 3 JUNE">03</div>
        <div class="tickets tickets_selector" data-value="WED 4 JUNE">04</div>
        <div class="tickets tickets_selector" data-value="THU 5 JUNE">05</div>
        <div class="tickets tickets_selector" data-value="FRI 6 JUNE">06</div>
        <div class="tickets tickets_selector" data-value="SAT 7 JUNE">07</div>
        <div class="tickets tickets_selector" data-value="SUN 8 JUNE">08</div>
      </div>

      <br>

      <hr class="tickets tickets_hr">

      <br>

      <span class="tickets tickets_title">Категорії:</span>
      <div class="category_select" data-select="count">
        <div class="tickets selector selector_selected" data-value="box">Box</div>
        <div class="tickets selector" data-value="category 1">Category 1</div>
        <div class="tickets selector" data-value="category 2">Category 2</div>
        <div class="tickets selector" data-value="category 3">Category 3</div>
        <div class="tickets selector" data-value="category gold">Category Gold</div>
      </div>

      <br>

      <span class="tickets tickets_title">Сесії:</span>
      <div class="session_select" data-select="count">
        <div class="tickets selector selector_selected" data-value="night">Night</div>
        <div class="tickets selector" data-value="day">Day</div>
        <div class="tickets selector" data-value="end of day">End of day</div>
      </div>

      <br>

      <span class="tickets tickets_title">Courts:</span>
      <div class="court_select" data-select="count">
        <div class="tickets selector selector_selected" data-value="Court Philippe-Chatrier">Court Philippe-Chatrier</div>
        <div class="tickets selector" data-value="Court Suzanne-Lenglen">Court Suzanne-Lenglen</div>
        <div class="tickets selector" data-value="Court Simonne-Mathieu">Court Simonne-Mathieu</div>
      </div>

      <br>

      <h2 class="tickets tickets_h2">Посилання на таблицю:</h2>
      <input type="text" placeholder="https://docs.google.com/spreadsheets/d/1TFE2R..." name="settings"class="tickets_input">

      <hr class="tickets tickets_hr">

      <br><br>

      <button class="tickets tickets_button" id="tickets_cancel">Назад</button>
      <button class="tickets tickets_button tickets_button_colored" id="tickets_start">Оновити налаштування</button>
    </div>
  </div>`,
    __settingsCSS: `.tickets {
      font-family: "Gill Sans", sans-serif;
    }

    .tickets_popup_wrapper {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba( 0, 0, 0, .5 );
      overflow: auto;
      z-index: 1000;
      display: none;
    }
    
    .tickets_data {
      display:block;
    }
    
    .tickets_data input {
      margin-right: 5px;
    }

    .tickets_popup {
      width: 500px;
      padding: 15px;
      box-sizing: border-box;
      margin: 50px auto;
      background: #fff;
      border-radius: 4px;
      position: relative;
    }

    .tickets_h1, .tickets_h2 {
      margin: 5px 0;
      font-weight: bold;
    }

    .tickets_h1 {
      font-size: 30px;
    }

    .tickets_h2 {
      font-size: 24px;
    }

    .tickets_select {
        display: inline-block;
    }

    .tickets_selector {
      margin: 3px 0;
      padding: 5px 15px;
      border: 1px solid #999;
      display: inline-block;
      border-radius: 4px;
      cursor: pointer;
      color: #555;
    }

    .tickets_selector:hover {
      background: rgba( 0, 0, 0, 0.05 );
    }

    .tickets_selector_selected {
      color: #000;
      font-weight: bold;
      border: 1px solid #2482f1;
    }

    .date_selector {
      margin: 3px 0;
      padding: 5px 15px;
      border: 1px solid #999;
      display: inline-block;
      border-radius: 4px;
      cursor: pointer;
      color: #555;
    }

    .date_selector:hover {
      background: rgba( 0, 0, 0, 0.05 );
    }

    .date_selector_selected {
      color: #000;
      font-weight: bold;
      border: 1px solid #2482f1;
    }

    .selector {
      margin: 3px 0;
      padding: 5px 15px;
      border: 1px solid #999;
      display: inline-block;
      border-radius: 4px;
      cursor: pointer;
      color: #555;
    }

    .selector:hover {
      background: rgba( 0, 0, 0, 0.05 );
    }

    .selector_selected {
      color: #000;
      font-weight: bold;
      border: 1px solid #2482f1;
    }

    .tickets_hr {
      width: 50%;
      border: 0;
      height: 1px;
      background: #aaa;
      margin: 10px auto;
    }

    .tickets_input {
      margin: 3px 0;
      padding: 5px 15px;
      border-radius: 4px;
      border: 1px solid #999;
      font-size: 16px;
      outline: none;
    }

    .tickets_input:focus {
        border: 1px solid #2482f1;
    }

    .tickets_title {
      margin-right: 10px;
    }

    .tickets_button {
      padding: 5px 15px;
      border: 1px solid #aaa;
      border-radius: 4px;
      font-size: 16px;
      cursor: pointer;
    }

    .tickets_button_colored {
      font-weight: bold;
      background: #2482f1;
      border: 1px solid #2482f1;
      color: #fff;
    }

    .tickets_notice {
        color: #555;
    }
		.settings-info{
			position: fixed;
			bottom: 15px;
			right: 15px;
			padding: 15px;
			background: #2482f1;
			color: #fff;
			width: 200px;
		}`,
    __settingsInfoCSS: `.settings-info{
      position: fixed;
      bottom: 15px;
      left: 15px;
      padding: 15px;
      background: #139df4;
      color: #fff;
      width: 300px;
      border-radius: 5px;
    }
    .settings-info p{
      font-family: 'Calibri';
      margin-bottom: 0;
    }`,
    __infoHTML: `<div class="settings-info" id="settings-info"></div>`,

    init: function () {
      console.log("in init");

      let style = document.createElement("style");
      style.innerText = UI.__settingsCSS;

      document.head.appendChild(style);

      // inject HTML
      const container = document.createElement("div");
      container.id = "settingsFormContainer";

      container.innerHTML = UI.__settingsHTML;

      document.body.appendChild(container);
      let categories = document.querySelectorAll(".selector");
      let tickets = document.querySelectorAll(
        ".tickets_select > .tickets_selector"
      );
      let dates = document.querySelectorAll(".date_select > .tickets_selector");
      let selectors = document.getElementsByClassName("tickets_selector");

      // AMOUNT
      if (settings.amount) {
        tickets.forEach((tempTicket) =>
          tempTicket.classList.remove("tickets_selector_selected")
        );

        for (let ticket of tickets) {
          if (ticket.getAttribute("data-value") == settings.amount) {
            ticket.classList.add("tickets_selector_selected");
            break;
          }
        }
      }

      // DATES
      for (var i = 0; i < dates.length; i++) {
        dates[i].onclick = function () {
          UI.select(this);
        };
      }

      if (settings.date) {
        let dates = document.querySelectorAll(
          ".date_select > .tickets_selector"
        );

        dates.forEach((tempDate) =>
          tempDate.classList.remove("tickets_selector_selected")
        );

        for (let date of dates) {
          if (date.getAttribute("data-value") == settings.date) {
            date.classList.add("tickets_selector_selected");
            break;
          }
        }
      }

      // CATEGORIES

      for (var i = 0; i < categories.length; i++) {
        categories[i].onclick = function () {
          UI.categorySelect(this);
        };
      }

      if (settings.categories) {
        categories.forEach((tempCategory) =>
          tempCategory.classList.remove("selector_selected")
        );

        for (let category of categories) {
          if (
            settings.categories.includes(category.textContent.toLowerCase()) ||
            settings.sessions.includes(category.textContent.toLowerCase()) ||
            settings.courts.includes(category.textContent)
          ) {
            category.classList.add("selector_selected");
          }
        }
      }

      // SELECTORS

      for (var i = 0; i < selectors.length; i++) {
        selectors[i].onclick = function () {
          UI.select(this);
        };
      }

      // GOOGLE SHEETS
      document.querySelector(
        'body > .tickets_popup_wrapper input[name="settings"]'
      ).value = settings.googleSheetsSettings
        ? settings.googleSheetsSettings
        : "";

      if (settings.googleSheetsSettings) {
        tickets.forEach((tempTicket) =>
          tempTicket.classList.remove("tickets_selector_selected")
        );
        categories.forEach((tempCategory) =>
          tempCategory.classList.remove("selector_selected")
        );
        dates.forEach((tempDate) =>
          tempDate.classList.remove("tickets_selector_selected")
        );
      }

      console.log(settings.googleSheetsSettings);

      // MAIN BUTTONS
      let cancel_button = document.getElementById("tickets_cancel");
      cancel_button.onclick = UI.closePopup;

      let start_button = document.getElementById("tickets_start");
      start_button.onclick = updateSettings;

      let wrapper = document.getElementsByClassName("tickets_popup_wrapper")[0];

      wrapper.onclick = function (event) {
        if (event.target.classList.contains("tickets_popup_wrapper"))
          UI.closePopup();
      };
    },

    openPopup: function () {
      let el = document.getElementsByClassName("tickets_popup_wrapper")[0];
      el.style.display = "block";
      document.body.style.overflow = "hidden";
    },

    closePopup: function () {
      let el = document.getElementsByClassName("tickets_popup_wrapper")[0];
      el.style.display = "none";
      document.body.style.overflow = "auto";
    },

    select: function (el) {
      let parent = el.parentNode;
      let els = parent.getElementsByClassName("tickets_selector");

      for (let i = 0; i < els.length; i++) {
        els[i].classList.remove("tickets_selector_selected");
      }

      el.classList.add("tickets_selector_selected");
    },

    categorySelect: function (el) {
      if (el.classList.contains("selector_selected")) {
        el.classList.remove("selector_selected");
      } else {
        el.classList.add("selector_selected");
      }
    },

    createButton: function (text, func) {
      var btn = document.createElement("a");
      btn.className = "rtc-reset-css tc-privacy-button";
      btn.style.fontFamily = "sans-serif";
      btn.innerHTML = text;
      btn.style.background = "#cc4e0e";
      btn.style.padding = "5px 10px";
      btn.style.color = "#fff";
      btn.style.position = "fixed";
      btn.style.right = "15px";
      btn.style.bottom = "15px";
      btn.style.cursor = "pointer";
      btn.style.letterSpacing = "1.2px";
      btn.style.fontWeight = "600";

      btn.onclick = function (e) {
        e.preventDefault();
        func();
      };

      document.body.appendChild(btn);
    },
  };

  function loadSettings() {
    console.log(db);
    const transaction = db.transaction("settings", "readwrite");
    const store = transaction.objectStore("settings");
    const getRequest = store.get(1);

    getRequest.onsuccess = function (event) {
      const storedSettings = event.target.result;
      if (storedSettings) {
        settings = storedSettings.settings;
        console.log("Loaded settings from IndexedDB:", settings);
      }
      UI.init();
      UI.createButton("Налаштування", UI.openPopup);
    };

    getRequest.onerror = function () {
      console.error("Error loading settings from IndexedDB.");
      UI.init();
      UI.createButton("Налаштування", UI.openPopup);
    };
  }

  /* Database logic */
  function updateSettings() {
    const amount = parseInt(
      document
        .querySelector(".tickets_select > .tickets_selector_selected")
        .getAttribute("data-value")
    );
    settings.amount = amount !== "" ? amount : null;
    const googleSheetsSettings = document.querySelector(
      'body > .tickets_popup_wrapper input[name="settings"]'
    ).value;
    const parentSelector = "body > div.tickets.tickets_popup_wrapper";

    const date = document
      .querySelector(".date_select > .tickets_selector_selected")
      .getAttribute("data-value");

    const categories = Array.from(
      document.querySelectorAll(
        parentSelector + " .category_select > div.selector_selected"
      )
    ).map((category) => {
      return category.getAttribute("data-value");
    });

    const sessions = Array.from(
      document.querySelectorAll(
        parentSelector + " .session_select > div.selector_selected"
      )
    ).map((category) => {
      return category.getAttribute("data-value");
    });

    const courts = Array.from(
      document.querySelectorAll(
        parentSelector + " .court_select > div.selector_selected"
      )
    ).map((category) => {
      return category.getAttribute("data-value");
    });

    settings.googleSheetsSettings = googleSheetsSettings;
    settings.date = date;
    settings.categories = categories;
    settings.sessions = sessions;
    settings.courts = courts;

    console.log(categories, sessions, courts, amount, date);

    // settings.selection = parseInt(document.getElementById("selection").value);
    settings.stopExecutionFlag = undefined;
    saveSettings(); // Save the updated settings to IndexedDB
    UI.closePopup();
  }

  function saveSettings() {
    settings.stopExecutionFlag = undefined;
    const transaction = db.transaction("settings", "readwrite");
    const store = transaction.objectStore("settings");
    store.put({ id: 1, settings: settings });

    transaction.oncomplete = function () {
      console.log("Settings updated in IndexedDB.");
      const backToMap = document.querySelector('a[id="backToMap1"]');
      if (backToMap) backToMap.click();
    };

    transaction.onerror = function () {
      console.error("Error updating settings in IndexedDB.");
    };
  }

  function init() {
    // Open IndexedDB and load stored settings if available
    const request = indexedDB.open("TicketBotDB", 2);

    request.onupgradeneeded = function (event) {
      db = event.target.result;
      if (!db.objectStoreNames.contains("settings")) {
        db.createObjectStore("settings", { keyPath: "id" });
      }
    };

    request.onsuccess = function (event) {
      db = event.target.result;
      loadSettings(); // Load settings from IndexedDB on success
    };

    request.onerror = function () {
      console.error("Error opening IndexedDB.");
    };
  }
  async function receive_sheets_data_main() {
    let SHEET_ID = "1hTGOnhHOszbPQf8YWsdqoR5m6EeDF0xs8pLPsabVXks";
    let SHEET_TITLE = "main";
    let SHEET_RANGE = "A2:H";
    let FULL_URL = `https://docs.google.com/spreadsheets/d/${SHEET_ID}/gviz/tq?sheet=${SHEET_TITLE}&range=${SHEET_RANGE}`;

    let dates = [];

    try {
      const text = await (await fetch(FULL_URL)).text();
      const {
        table: { rows },
      } = JSON.parse(text.slice(47, -2));

      const result = rows.map(({ c }) => ({
        date: c[0]?.v,
        courts: c[1]?.v.split(", "),
        categories: [
          { cat3: c[2]?.v },
          { cat2: c[3]?.v },
          { cat1: c[4]?.v },
          { gold: c[5]?.v },
          { box: c[6]?.v },
        ],
      }));
      console.log(result);
      return result;
    } catch (error) {
      console.error("Error fetching data:", error);
      return null;
    }
  }

  // init();
  (async () => receive_sheets_data_main())();
};
