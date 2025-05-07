from filtration import filter_seats
import random
polygon_ids = ["121413","121414","1120","121412","121446","121447","121301","121305","121309"]
amount = 2
print(polygon_ids)
if not polygon_ids: 
    print('no seat available')


if int(amount) > 1:
    filtered_seats = filter_seats(polygon_ids, amount)
    print(filtered_seats)
    if not filtered_seats: 
        print('Not enough seats found')
    random_seats_arr = max(filtered_seats, key=len) if filtered_seats else []
    for seat_id in random_seats_arr:
        print(f'polygon[class="polygon"][id="{seat_id}"]')
        # seat = await check_for_element(page, f'polygon[class="polygon"][id="{seat_id}"]', debug=True)
        # if not seat: break
        # await seat.mouse_move()
        # time.sleep(1)
        # await seat.mouse_click()
        # time.sleep(1)
        # await get_stadion_ticket(page)
        # print('after click')