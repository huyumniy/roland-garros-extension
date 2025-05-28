export const findBiggestArray = arr => arr.reduce((a, b) => b.length > a.length ? b : a, []);

export const convertToPayload = (arr, priceId) => {
  return arr.map(seat => ({
    seatId: seat,
    priceId: priceId,
  }));
}
