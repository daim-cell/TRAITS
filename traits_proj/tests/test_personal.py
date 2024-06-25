from traits.implementation import Traits, TraitsUtility
from traits.interface import TraitsKey, TrainStatus, SortingCriteria
import pytest

def set_up(t, starting_station_key, ending_station_key, 
           train_key, starting_hours_24_h, starting_minutes, 
           valid_from_day, valid_from_month, valid_from_year,
           valid_until_day, valid_until_month, valid_until_year):
    
    t.add_train_station(starting_station_key, None)
    t.add_train_station(ending_station_key, None)
    
    t.add_train(train_key, train_capacity=3, train_status=TrainStatus.OPERATIONAL)

    t.connect_train_stations(starting_station_key, ending_station_key, 40)

    # Stops
    stops = []
    # The train waits 5 minutes at first station
    stops.append( (starting_station_key, 5) )
    # This is not possible, since the stations are NOT connected
    stops.append( (ending_station_key, 10) )
    

    t.add_schedule(
                train_key,
                starting_hours_24_h, starting_minutes,
                stops,
                valid_from_day, valid_from_month, valid_from_year,
                valid_until_day, valid_until_month, valid_until_year)
    

def test_search_connections_success(rdbms_connection, rdbms_admin_connection, neo4j_db):
    # utility_mock = create_autospec(TraitsUtility)
    t = Traits(rdbms_connection, rdbms_admin_connection, neo4j_db)


    starting_station_key = TraitsKey("1")
    middle_station_key = TraitsKey("2")
    ending_station_key = TraitsKey("3")

    t.add_train_station(starting_station_key, None)
    t.add_train_station(middle_station_key, None)
    t.add_train_station(ending_station_key, None)
    train_key = TraitsKey('t1')
    t.add_train(train_key, train_capacity=100, train_status=TrainStatus.OPERATIONAL)

    t.connect_train_stations(starting_station_key, middle_station_key, 40)
    t.connect_train_stations(middle_station_key, ending_station_key, 60)

    # Stops
    stops = []
    # The train waits 5 minutes at first station
    stops.append( (starting_station_key, 5) )
    stops.append( (middle_station_key, 8) )
    # This is not possible, since the stations are NOT connected
    stops.append( (ending_station_key, 10) )
    starting_hours_24_h, starting_minutes = 8, 0

    
    valid_from_day, valid_from_month, valid_from_year = 1, 1, 2024
    valid_until_day, valid_until_month, valid_until_year = 3, 1, 2024

    t.add_schedule(
                train_key,
                starting_hours_24_h, starting_minutes,
                stops,
                valid_from_day, valid_from_month, valid_from_year,
                valid_until_day, valid_until_month, valid_until_year)
    
   
    
    results = t.search_connections(starting_station_key, ending_station_key, valid_from_day, valid_from_month, valid_from_year)
    test_final = []
    for result in results:
        test_final.append([result[0][0], result[1][0]])

    # Based on the test the trip ids should be from the first day then second and then third day
    assert test_final == [[1, 2], [3, 4], [5, 6]]

def test_search_connections_with_price_n_numtrians(rdbms_connection, rdbms_admin_connection, neo4j_db):
    # utility_mock = create_autospec(TraitsUtility)
    t = Traits(rdbms_connection, rdbms_admin_connection, neo4j_db)


    starting_station_key = TraitsKey("1")
    middle_station_key = TraitsKey("2")
    ending_station_key = TraitsKey("3")

    t.add_train_station(starting_station_key, None)
    t.add_train_station(middle_station_key, None)
    t.add_train_station(ending_station_key, None)
    train_key = TraitsKey('t1')
    train_key2 = TraitsKey('t2')
    t.add_train(train_key, train_capacity=100, train_status=TrainStatus.OPERATIONAL)
    t.add_train(train_key2, train_capacity=50, train_status=TrainStatus.OPERATIONAL)
    t.connect_train_stations(starting_station_key, middle_station_key, 20)
    t.connect_train_stations(middle_station_key, ending_station_key, 20)
    t.connect_train_stations(starting_station_key, ending_station_key, 60)

    # Stops
    stops = []
    # The train waits 5 minutes at first station
    stops.append( (starting_station_key, 5) )
    stops.append( (middle_station_key, 8) )
    # This is not possible, since the stations are NOT connected
    stops.append( (ending_station_key, 10) )
    starting_hours_24_h, starting_minutes = 8, 0

    sch = []
    sch.append( (starting_station_key, 5) )
    sch.append( (ending_station_key, 10) )

    # The schedule is valid from 1 jan to 31 dec 2024
    valid_from_day, valid_from_month, valid_from_year = 6, 1, 2024
    valid_until_day, valid_until_month, valid_until_year = 6, 1, 2024

    t.add_schedule(
                train_key,
                starting_hours_24_h, starting_minutes,
                stops,
                valid_from_day, valid_from_month, valid_from_year,
                valid_until_day, valid_until_month, valid_until_year)
    
    t.add_schedule(
                train_key2,
                starting_hours_24_h, starting_minutes,
                sch,
                valid_from_day, valid_from_month, valid_from_year,
                valid_until_day, valid_until_month, valid_until_year)
    
   
    
    result_price = t.search_connections(starting_station_key, ending_station_key, valid_from_day, valid_from_month, valid_from_year, sort_by=SortingCriteria.ESTIMATED_PRICE, limit=3)
    test_final = []
    for result in result_price:
        arr = []
        for res in result:
            arr.append(res[0])
        test_final.append(arr)

    assert test_final == [[1, 2], [3]]
    
    result_numtrains = t.search_connections(starting_station_key, ending_station_key, valid_from_day, valid_from_month, valid_from_year, sort_by=SortingCriteria.NUMBER_OF_TRAIN_CHANGES, limit=3)
    test_final = []
    for result in result_numtrains:
        arr = []
        for res in result:
            arr.append(res[0])
        test_final.append(arr)
    # Shorter trip is returned first as the price is less, however for number of train changes return the longer trip as it is a single trip 
    assert test_final == [[3], [1, 2]]

def test_schedule_overlap(rdbms_connection, rdbms_admin_connection, neo4j_db):
    # utility_mock = create_autospec(TraitsUtility)
    t = Traits(rdbms_connection, rdbms_admin_connection, neo4j_db)


    starting_station_key = TraitsKey("1")
    middle_station_key = TraitsKey("2")
    ending_station_key = TraitsKey("3")

    t.add_train_station(starting_station_key, None)
    t.add_train_station(middle_station_key, None)
    t.add_train_station(ending_station_key, None)
    train_key = TraitsKey('t1')
    t.add_train(train_key, train_capacity=100, train_status=TrainStatus.OPERATIONAL)
    t.connect_train_stations(starting_station_key, middle_station_key, 20)
    t.connect_train_stations(middle_station_key, ending_station_key, 20)
    t.connect_train_stations(starting_station_key, ending_station_key, 60)

    # Stops
    stops = []
    # The train waits 5 minutes at first station
    stops.append( (starting_station_key, 5) )
    stops.append( (middle_station_key, 8) )
    # This is not possible, since the stations are NOT connected
    stops.append( (ending_station_key, 10) )
    starting_hours_24_h, starting_minutes = 8, 0

    sch = []
    sch.append( (starting_station_key, 5) )
    sch.append( (ending_station_key, 10) )

    # The schedule is valid from 1 jan to 31 dec 2024
    valid_from_day, valid_from_month, valid_from_year = 6, 1, 2024
    valid_until_day, valid_until_month, valid_until_year = 6, 1, 2024

    t.add_schedule(
                train_key,
                starting_hours_24_h, starting_minutes,
                stops,
                valid_from_day, valid_from_month, valid_from_year,
                valid_until_day, valid_until_month, valid_until_year)
    with pytest.raises(ValueError):
        t.add_schedule(
                    train_key,
                    8, 30,
                    sch,
                    valid_from_day, valid_from_month, valid_from_year,
                    valid_until_day, valid_until_month, valid_until_year) 
        
    with pytest.raises(ValueError):
        t.add_schedule(
                    train_key,
                    7, 30,
                    sch,
                    valid_from_day, valid_from_month, valid_from_year,
                    valid_until_day, valid_until_month, valid_until_year) 

def test_search_connections_same_station(rdbms_connection, rdbms_admin_connection, neo4j_db):
    t = Traits(rdbms_connection, rdbms_admin_connection, neo4j_db)

    starting_station_key = TraitsKey("1")
    ending_station_key = TraitsKey("1")

    with pytest.raises(ValueError):
        t.search_connections(starting_station_key, ending_station_key)

def test_get_train_current_status_exists(rdbms_connection, rdbms_admin_connection, neo4j_db):
    
    train_key = TraitsKey('Train1')
    t = Traits(rdbms_connection, rdbms_admin_connection, neo4j_db)
    t.add_train(train_key, train_capacity=100, train_status=TrainStatus.OPERATIONAL)
    result1 = t.get_train_current_status(TraitsKey("Train1"))
    assert result1 == TrainStatus.OPERATIONAL
    t.update_train_details(train_key, train_status = TrainStatus.DELAYED)
    # print(result)
    result2 = t.get_train_current_status(TraitsKey("Train1"))
    assert result2 == TrainStatus.DELAYED
   
def test_buy_ticket_success(rdbms_connection, rdbms_admin_connection, neo4j_db):


    t = Traits(rdbms_connection, rdbms_admin_connection, neo4j_db)
    starting_station_key = TraitsKey("1")
    ending_station_key = TraitsKey("2")
    train_key = TraitsKey('t1')
    starting_hours_24_h, starting_minutes = 8, 0

    # The schedule is valid from 1 jan to 31 dec 2024
    valid_from_day, valid_from_month, valid_from_year = 1, 1, 2024
    valid_until_day, valid_until_month, valid_until_year = 1, 1, 2024
    set_up(t, starting_station_key, ending_station_key, train_key, starting_hours_24_h, starting_minutes, valid_from_day, valid_from_month, valid_from_year,valid_until_day, valid_until_month, valid_until_year)
    
    result = t.search_connections(starting_station_key, ending_station_key, valid_from_day, valid_from_month, valid_from_year)
   
    t.add_user("user@example.com", None)
    tick = t.buy_ticket("user@example.com", result[0][0], also_reserve_seats=True)
    # print(tick)
    #The reservtion id of the the ticket bought
    assert tick == 1
    tick2 = t.buy_ticket("user@example.com", result[0][0], also_reserve_seats=False)
    tick3 = t.buy_ticket("user@example.com", result[0][0], also_reserve_seats=False)
    assert tick2 == 2 and tick3 == 3

def test_buy_ticket_reservation(rdbms_connection, rdbms_admin_connection, neo4j_db):
    t = Traits(rdbms_connection, rdbms_admin_connection, neo4j_db)
    starting_station_key = TraitsKey("1")
    ending_station_key = TraitsKey("2")
    train_key = TraitsKey('t1')
    starting_hours_24_h, starting_minutes = 8, 0

    # The schedule is valid from 1 jan to 31 dec 2024
    valid_from_day, valid_from_month, valid_from_year = 1, 1, 2024
    valid_until_day, valid_until_month, valid_until_year = 1, 1, 2024
    set_up(t, starting_station_key, ending_station_key, train_key, starting_hours_24_h, starting_minutes, valid_from_day, valid_from_month, valid_from_year,valid_until_day, valid_until_month, valid_until_year)
    
    result = t.search_connections(starting_station_key, ending_station_key, valid_from_day, valid_from_month, valid_from_year)
   
    t.add_user("user@example.com", None)
    t.buy_ticket("user@example.com", result[0][0], also_reserve_seats=True)
    t.buy_ticket("user@example.com", result[0][0], also_reserve_seats=True)
    t.buy_ticket("user@example.com", result[0][0], also_reserve_seats=True)
    # print(tick)
    #The ticket id of the the ticket bought
    t.add_user("user2@example.com", None)
    with pytest.raises(ValueError):
        t.buy_ticket("user2@example.com", result[0][0], also_reserve_seats=True)

def test_user_with_no_purchase_history(rdbms_connection, rdbms_admin_connection, neo4j_db):


    t = Traits(rdbms_connection, rdbms_admin_connection, neo4j_db)
    t.add_user("user@example.com", None)
    history = t.get_purchase_history("user@example.com")
    # No ticket bought yet
    assert history == []

def test_purchase_history_success(rdbms_connection, rdbms_admin_connection, neo4j_db):


    t = Traits(rdbms_connection, rdbms_admin_connection, neo4j_db)
    starting_station_key = TraitsKey("1")
    ending_station_key = TraitsKey("2")
    train_key = TraitsKey('t1')
    starting_hours_24_h, starting_minutes = 8, 0

    # The schedule is valid from 1 jan to 31 dec 2024
    valid_from_day, valid_from_month, valid_from_year = 1, 1, 2024
    valid_until_day, valid_until_month, valid_until_year = 1, 1, 2024
    set_up(t, starting_station_key, ending_station_key, train_key, starting_hours_24_h, starting_minutes, valid_from_day, valid_from_month, valid_from_year,valid_until_day, valid_until_month, valid_until_year)
    
    result = t.search_connections(starting_station_key, ending_station_key, valid_from_day, valid_from_month, valid_from_year)
    user_mail = "user@example.com"
    t.add_user(user_mail, None)
    t.buy_ticket(user_mail, result[0][0], also_reserve_seats=True)
    history = t.get_purchase_history(user_mail)
    #The ticket id of the the ticket bought
    assert history[0][1] == 1
  
def test_invalid_delete_user(rdbms_connection, rdbms_admin_connection, neo4j_db):
    t = Traits(rdbms_connection, rdbms_admin_connection, neo4j_db)
    # The user doesnt exist
    with pytest.raises(ValueError):
        t.delete_user("user2@example.com")

def test_add_train_without_permission(rdbms_connection, rdbms_admin_connection, neo4j_db):
    t = Traits(rdbms_connection, rdbms_connection, neo4j_db)
    # The permission is not there
    with pytest.raises(ValueError):
        rec = t.add_train(TraitsKey('T2'), 50, TrainStatus.OPERATIONAL)
   
def test_add_train_station_success(rdbms_connection, rdbms_admin_connection, neo4j_db):
    t = Traits(rdbms_connection, rdbms_admin_connection, neo4j_db)
    station_key = TraitsKey("station_1")
    
    t.add_train_station(station_key, None)
    
    cursor = rdbms_connection.cursor()
    cursor.execute("SELECT station_id FROM Stations WHERE name = %s", (station_key.to_string(),))
    station_id = cursor.fetchone()
    assert station_id is not None

def test_add_train_station_failure(rdbms_connection, rdbms_admin_connection, neo4j_db):
    t = Traits(rdbms_connection, rdbms_admin_connection, neo4j_db)
    station_key = TraitsKey("station_1")
    
    t.add_train_station(station_key, None)
    
    with pytest.raises(ValueError):
        t.add_train_station(station_key, None)  # Trying to add the same station again should raise an error

def test_connect_train_stations_success(rdbms_connection, rdbms_admin_connection, neo4j_db):
    t = Traits(rdbms_connection, rdbms_admin_connection, neo4j_db)
    station_key_1 = TraitsKey("1")
    station_key_2 = TraitsKey("2")
    travel_time = 30
    
    t.add_train_station(station_key_1, None)
    t.add_train_station(station_key_2, None)
    t.connect_train_stations(station_key_1, station_key_2, travel_time)
    
    cursor = rdbms_admin_connection.cursor()
    cursor.execute("SELECT * FROM Connections WHERE starting_station = %s AND ending_station = %s", 
                   (station_key_1.to_string(), station_key_2.to_string()))
    connection = cursor.fetchone()
    assert connection is not None

def test_connect_train_stations_failure(rdbms_connection, rdbms_admin_connection, neo4j_db):
    t = Traits(rdbms_connection, rdbms_admin_connection, neo4j_db)
    station_key_1 = TraitsKey("station_1")
    station_key_2 = TraitsKey("station_2")
    travel_time = 30
    
    with pytest.raises(ValueError):
        t.connect_train_stations(station_key_1, station_key_2, travel_time)  # Stations do not exist yet

def test_add_schedule_no_connection(rdbms_connection, rdbms_admin_connection, neo4j_db):
    t = Traits(rdbms_connection, rdbms_admin_connection, neo4j_db)
    train_key = TraitsKey("train_1")
    t.add_train(train_key, 100, TrainStatus.OPERATIONAL)
    t.add_train_station(TraitsKey("station_1"), None)
    t.add_train_station(TraitsKey("station_2"), None)
    
    stops = [(TraitsKey("station_1"), 5), (TraitsKey("station_2"), 10)]
    with pytest.raises(ValueError):
     t.add_schedule(train_key, 8, 0, stops, 1, 1, 2024, 31, 12, 2024)
    
def test_add_schedule_failure(rdbms_connection, rdbms_admin_connection, neo4j_db):
    t = Traits(rdbms_connection, rdbms_admin_connection, neo4j_db)
    train_key = TraitsKey("train_1")
    t.add_train_station(TraitsKey("station_1"), None)
    t.add_train_station(TraitsKey("station_2"), None)
    stops = [(TraitsKey("station_1"), 5), (TraitsKey("station_2"), 10)]
    
    with pytest.raises(ValueError):
        t.add_schedule(train_key, 8, 0, stops, 1, 1, 2024, 31, 12, 2024)  # Train does not exist yet

def test_add_user_invalid_email_format(rdbms_connection, rdbms_admin_connection, neo4j_db):
    t = Traits(rdbms_connection, rdbms_admin_connection, neo4j_db)
    invalid_email = "invalid_email_format"

    with pytest.raises(ValueError):
        t.add_user(invalid_email, None)

# def test_delete_user(rdbms_connection, rdbms_admin_connection, neo4j_db):
#     t = Traits(rdbms_connection, rdbms_admin_connection, neo4j_db)
    
#     starting_station_key = TraitsKey("1")
#     ending_station_key = TraitsKey("2")
#     train_key = TraitsKey('t1')
#     starting_hours_24_h, starting_minutes = 8, 0

#     # The schedule is valid from 1 jan to 31 dec 2024
#     valid_from_day, valid_from_month, valid_from_year = 1, 1, 2024
#     valid_until_day, valid_until_month, valid_until_year = 1, 1, 2024
#     set_up(t, starting_station_key, ending_station_key, train_key, starting_hours_24_h, starting_minutes, valid_from_day, valid_from_month, valid_from_year,valid_until_day, valid_until_month, valid_until_year)
    
#     result = t.search_connections(starting_station_key, ending_station_key, valid_from_day, valid_from_month, valid_from_year)
   
#     user_email = "user@example.com"
#     t.add_user(user_email, None)
#     t.buy_ticket(user_email, result[0][0], also_reserve_seats=True)
#     assert len(t.get_purchase_history(user_email)) == 1

#     t.delete_user(user_email)

#     # Check that user's data is deleted
#     assert len(t.get_purchase_history(user_email)) == 0
#     cursor = rdbms_admin_connection.cursor()
#     cursor.execute("""SELECT * FROM Reservations r 
#                    JOIN Tickets tk WHERE tk.ticket_id = r.ticket_id
#                     WHERE t.email = %s """, (user_email,))
#     rec = cursor.fetchall()
#     assert rec == 0

# def test_delete_train(rdbms_connection, rdbms_admin_connection, neo4j_db):
#     t = Traits(rdbms_connection, rdbms_admin_connection, neo4j_db)
#     train_key = TraitsKey("train_to_delete")
#     t.add_train(train_key, 100, TrainStatus.OPERATIONAL)
#     t.add_train_station(TraitsKey("1"), None)
#     t.add_train_station(TraitsKey("2"), None)
#     stops = [(TraitsKey("1"), 5), (TraitsKey("2"), 10)]
#     t.connect_train_stations(TraitsKey("1"), TraitsKey("2"), 40)
#     t.add_schedule(train_key, 8, 0, stops, 1, 1, 2024, 1, 2, 2024)
#     result = t.search_connections(TraitsKey("1"), TraitsKey("2"), 1, 1, 2024)
   
#     user_email = "user@example.com"
#     t.add_user(user_email, None)
#     t.buy_ticket(user_email, result[0][0], also_reserve_seats=True)
#     assert len(t.get_purchase_history(user_email)) == 1

#     t.delete_train(train_key)

#     # Check that train's schedules are canceled
#     assert len(t.search_connections(TraitsKey("1"), TraitsKey("2"), 1, 1, 2024)) == 0
#     # Check that future reservations are canceled
    
#     cursor = rdbms_admin_connection.cursor()
#     cursor.execute("""SELECT * FROM Reservations r 
#                    JOIN Tickets tk WHERE tk.ticket_id = r.ticket_id 
#                    JOIN Trips t WHERE tk.trip_id = t.trip_id WHERE t.train_id = %s """, (train_key.to_string(),))
#     rec = cursor.fetchall()
#     assert rec == 0

#     assert len(t.get_purchase_history(user_email)) == 1
 
def test_train_stops_at_all_stations(rdbms_connection, rdbms_admin_connection, neo4j_db):
    t = Traits(rdbms_connection, rdbms_admin_connection, neo4j_db)
    station_key_1 = TraitsKey("1")
    station_key_2 = TraitsKey("2")
    station_key_3 = TraitsKey("3")
    t.add_train_station(station_key_1, None)
    t.add_train_station(station_key_2, None)
    t.add_train_station(station_key_3, None)
    t.connect_train_stations(station_key_1, station_key_2, 40)
    t.connect_train_stations(station_key_2, station_key_3, 40)
    stops = [(station_key_1, 5), (station_key_3, 10)]
    train_key = TraitsKey("train_with_invalid_stops")
    t.add_train(train_key, 100, TrainStatus.OPERATIONAL)
    with pytest.raises(ValueError):
        t.add_schedule(train_key, 8, 0, stops, 1, 1, 2024, 1, 1, 2024)

def test_night_operations1(rdbms_connection, rdbms_admin_connection, neo4j_db):
    t = Traits(rdbms_connection, rdbms_admin_connection, neo4j_db)
    
    # Add stations and a train with schedules spanning two days
    station_key_1 = TraitsKey("1")
    station_key_2 = TraitsKey("2")
    t.add_train_station(station_key_1, None)
    t.add_train_station(station_key_2, None)
    t.connect_train_stations(station_key_1, station_key_2, 30)
    train_key = TraitsKey("train_1")
    t.add_train(train_key, 100, TrainStatus.OPERATIONAL)
    stops_day1 = [(station_key_1, 5), (station_key_2, 10)]
    stops_day2 = [(station_key_2, 5), (station_key_1, 10)]
    # Schedule spanning two days
    t.add_schedule(train_key, 22, 0, stops_day1, 1, 1, 2024, 1, 1, 2024)
    t.add_schedule(train_key, 8, 0, stops_day2, 1, 1, 2024, 2, 1, 2024)
    
    # Verify that the last stop of day 1 is at least 6 hours before the first stop of day 2
    schedules = t.utility.get_all_schedules()
    assert len(schedules) == 2
    # Adding a schedule that is within six hours of a schedule of a previous day
    with pytest.raises(ValueError):
        t.add_schedule(train_key, 3, 0, stops_day2, 2, 1, 2024, 2, 1, 2024)

def test_night_operations2(rdbms_connection, rdbms_admin_connection, neo4j_db):
    t = Traits(rdbms_connection, rdbms_admin_connection, neo4j_db)
    
    # Add stations and a train with schedules spanning two days
    station_key_1 = TraitsKey("1")
    station_key_2 = TraitsKey("2")
    t.add_train_station(station_key_1, None)
    t.add_train_station(station_key_2, None)
    t.connect_train_stations(station_key_1, station_key_2, 30)
    train_key = TraitsKey("train_1")
    t.add_train(train_key, 100, TrainStatus.OPERATIONAL)
    stops_day1 = [(station_key_1, 5), (station_key_2, 10)]
    stops_day2 = [(station_key_2, 5), (station_key_1, 10)]
    # Schedule spanning two days
    
    t.add_schedule(train_key, 8, 0, stops_day2, 1, 1, 2024, 2, 1, 2024)
    t.add_schedule(train_key, 3, 0, stops_day2, 2, 1, 2024, 2, 1, 2024)
    
    # Verify that the last stop of day 1 is at least 6 hours before the first stop of day 2
    schedules = t.utility.get_all_schedules()
    assert len(schedules) == 2
    # Adding a schedule that is within six hours of a schedule of a next day
    with pytest.raises(ValueError):
        t.add_schedule(train_key, 22, 0, stops_day1, 1, 1, 2024, 1, 1, 2024)

def test_add_schedule_complex(rdbms_connection, rdbms_admin_connection, neo4j_db):
    t = Traits(rdbms_connection, rdbms_admin_connection, neo4j_db)
    
    # Add stations
    t.add_train_station(TraitsKey("station_A"), None)
    t.add_train_station(TraitsKey("station_B"), None)
    t.add_train_station(TraitsKey("station_C"), None)
    t.add_train_station(TraitsKey("station_D"), None)
    
    # Add train
    train_key = TraitsKey("train_X")
    t.add_train(train_key, 100, TrainStatus.OPERATIONAL)
    
    # Connect stations
    t.connect_train_stations(TraitsKey("station_A"), TraitsKey("station_B"), 20)
    t.connect_train_stations(TraitsKey("station_B"), TraitsKey("station_C"), 30)
    t.connect_train_stations(TraitsKey("station_C"), TraitsKey("station_D"), 25)
    
    # Define stops and schedule dates
    stops = [(TraitsKey("station_A"), 5), (TraitsKey("station_B"), 10), (TraitsKey("station_C"), 5), (TraitsKey("station_D"), 10)]
    valid_from_day, valid_from_month, valid_from_year = 1, 1, 2025
    valid_until_day, valid_until_month, valid_until_year = 3, 1, 2025
    
    # Add schedule
    t.add_schedule(train_key, 8, 0, stops, valid_from_day, valid_from_month, valid_from_year, valid_until_day, valid_until_month, valid_until_year)
    
    # Check if the schedule was added correctly
    trips = t.search_connections(TraitsKey("station_B"), TraitsKey("station_D"), 1, 1, 2024)
    assert len(trips) == 3 and len(trips[0])==2  # Three trips should be created (one for each day)
    
def test_schedule_not_end_same_day(rdbms_connection, rdbms_admin_connection, neo4j_db):
    t = Traits(rdbms_connection, rdbms_admin_connection, neo4j_db)
    
    # Add stations and a train with schedules spanning two days
    station_key_1 = TraitsKey("1")
    station_key_2 = TraitsKey("2")
    t.add_train_station(station_key_1, None)
    t.add_train_station(station_key_2, None)
    t.connect_train_stations(station_key_1, station_key_2, 60)
    train_key = TraitsKey("train_1")
    t.add_train(train_key, 100, TrainStatus.OPERATIONAL)
    stops_day1 = [(station_key_1, 5), (station_key_2, 10)]
    # Schedule spanning two days
    
    # Adding a schedule that is within six hours of a schedule of a previous day
    with pytest.raises(ValueError):
        t.add_schedule(train_key, 23, 30, stops_day1, 1, 1, 2024, 1, 1, 2024)

def test_schedule_overlap_multiple(rdbms_connection, rdbms_admin_connection, neo4j_db):
    # utility_mock = create_autospec(TraitsUtility)
    t = Traits(rdbms_connection, rdbms_admin_connection, neo4j_db)


    starting_station_key = TraitsKey("1")
    middle_station_key = TraitsKey("2")
    ending_station_key = TraitsKey("3")

    t.add_train_station(starting_station_key, None)
    t.add_train_station(middle_station_key, None)
    t.add_train_station(ending_station_key, None)
    train_key = TraitsKey('t1')
    t.add_train(train_key, train_capacity=100, train_status=TrainStatus.OPERATIONAL)
    t.connect_train_stations(starting_station_key, middle_station_key, 30)
    t.connect_train_stations(middle_station_key, ending_station_key, 30)
    t.connect_train_stations(starting_station_key, ending_station_key, 60)

    # Stops
    stops = []
    # The train waits 5 minutes at first station
    stops.append( (starting_station_key, 10) )
    stops.append( (middle_station_key, 10) )
    # This is not possible, since the stations are NOT connected
    stops.append( (ending_station_key, 10) )

    sch = []
    sch.append( (starting_station_key, 5) )
    sch.append( (ending_station_key, 10) )

    # The schedule is valid from 1 jan to 31 dec 2024
    valid_from_day, valid_from_month, valid_from_year = 6, 1, 2024
    valid_until_day, valid_until_month, valid_until_year = 6, 1, 2024

    t.add_schedule(
                train_key,
                8, 0,
                stops,
                valid_from_day, valid_from_month, valid_from_year,
                valid_until_day, valid_until_month, valid_until_year)
    t.add_schedule(
                train_key,
                18, 0,
                stops,
                valid_from_day, valid_from_month, valid_from_year,
                valid_until_day, valid_until_month, valid_until_year)
    assert len(t.utility.get_all_schedules()) == 2
    with pytest.raises(ValueError):
        t.add_schedule(
                    train_key,
                    8, 30,
                    sch,
                    valid_from_day, valid_from_month, valid_from_year,
                    valid_until_day, valid_until_month, valid_until_year) 
