// https://tickets.rolandgarros.com/api/v2/en/ticket/calendar/offers-grouped-by-sorted-offer-type/2025-05-25

export const date = [
  {
    offerType: {
      title: "Day ticket",
      position: 1,
      mention: "",
      description:
        "Attend the largest clay court tournament in the world on one day.",
      offerType: "SINGLE_DAY", // DAY TICKET
    },
    offers: [
      {
        offerId: 42,
        familyId: 1,
        sessionTypes: "JOU", // day session
        court: "PC", // Court Philippe-Chatrier
        title: "Single ticket",
        description:
          '<p>Reserved seat on the court <span style="color: rgb(230, 81, 0)">for&nbsp;the Day session matches</span>.</p><p><br></p><p>Unlimited access to the outside courts in free seating.&nbsp;</p>',
        minPrice: 0.0,
        imageUrl:
          "https://images.prismic.io/fft-billetterie/e0125636-1378-41ef-a087-b0c3d31a6ee6_Screenshot_3.png?auto=compress,format",
        sessionsDatesLabel: "Monday 26 May",
        sessions: [
          {
            dateLongDescription: "Monday 26 May",
            longDescription:
              '<p><u><span style="color: rgb(80, 80, 80)">From 12PM<br></span></u><span style="color: rgb(80, 80, 80)">1st round Ladies\' &amp; Gentlemen\'s Singles<br>| 3 matches</span></p>',
            court: "PC",
            sessionType: "JOU",
          },
        ],
        sessionIds: [2605],
        isAvailable: false,
        offerType: "SINGLE_DAY",
      },
      {
        offerId: 47,
        familyId: 1,
        sessionTypes: "SOI", // night session
        court: "PC",
        title: "Single ticket",
        description:
          '<p><span>Reserved seat on the court for&nbsp;</span><span style="color: #e65100">the match of the Night session</span><span>,&nbsp;not before 8:00pm.</span></p><p><span><br></span></p><p><span>Access to the stadium from 6:30PM.&nbsp;</span></p>',
        minPrice: 110.0,
        imageUrl:
          "https://images.prismic.io/fft-billetterie/36a2e9a6-6752-48ed-84be-d870dbdc0ba3_20230603_RG_NG_25479_web.jpg?auto=compress,format",
        sessionsDatesLabel: "Monday 26 May",
        sessions: [
          {
            dateLongDescription: "Monday 26 May",
            longDescription:
              '<p><u><span style="color: rgb(80, 80, 80)">Not before 8:15PM<br></span></u><span style="color: rgb(80, 80, 80)">1st round Ladies\' or Gentlemen\'s Singles<br>| 1 "Great" match</span></p>',
            court: "PC",
            sessionType: "SOI",
          },
        ],
        sessionIds: [2677],
        isAvailable: true, // zones.js continue condition
        offerType: "SINGLE_DAY",
      },
    ],
    premiumOffers: [],
    isOfferTypeAvailable: true, // do not iterrate offers if false
  },
];
