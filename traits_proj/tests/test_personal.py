from traits.implementation import Traits, TraitsUtility
from traits.interface import TraitsKey, TrainStatus, SortingCriteria
import pytest

def set_up(t, starting_station_key, ending_station_key, 
           train_key, starting_hours_24_h, starting_minutes, 
           valid_from_day, valid_from_month, valid_from_year,
           valid_until_day, valid_until_month, valid_until_year):
    
    t.add_train_station(starting_station_key, None)
    t.add_train_station(ending_station_key, None)
    
    t.add_train(train_key, train_capacity=1, train_status=TrainStatus.OPERATIONAL)

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

    # The schedule is valid from 1 jan to 31 dec 2024
    valid_from_day, valid_from_month, valid_from_year = 1, 1, 2024
    valid_until_day, valid_until_month, valid_until_year = 3, 1, 2024

    t.add_schedule(
                train_key,
                starting_hours_24_h, starting_minutes,
                stops,
                valid_from_day, valid_from_month, valid_from_year,
                valid_until_day, valid_until_month, valid_until_year)
    
   
    
    result = t.search_connections(starting_station_key, ending_station_key, valid_from_day, valid_from_month, valid_from_year)
    print(result)
    # Based on the test the trip ids should be from the first day then second and then third day
    assert result == [[1, 2], [3, 4], [5, 6]]

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
    valid_from_day, valid_from_month, valid_from_year = 1, 1, 2024
    valid_until_day, valid_until_month, valid_until_year = 1, 1, 2024

    t.add_schedule(
                train_key,
                starting_hours_24_h, starting_minutes,
                stops,
                valid_from_day, valid_from_month, valid_from_year,
                valid_until_day, valid_until_month, valid_until_year)
    
    t.add_schedule(
                train_key,
                starting_hours_24_h, starting_minutes,
                sch,
                valid_from_day, valid_from_month, valid_from_year,
                valid_until_day, valid_until_month, valid_until_year)
    
   
    
    result_price = t.search_connections(starting_station_key, ending_station_key, valid_from_day, valid_from_month, valid_from_year, sort_by=SortingCriteria.ESTIMATED_PRICE, limit=3)
    assert result_price == [[1, 2], [3]]
    
    result_numtrains = t.search_connections(starting_station_key, ending_station_key, valid_from_day, valid_from_month, valid_from_year, sort_by=SortingCriteria.NUMBER_OF_TRAIN_CHANGES, limit=3)
    # Shorter trip is returned first as the price is less, however for number of train changes return the longer trip as it is a single trip 
    assert result_numtrains == [[3], [1, 2]]

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
    #The ticket id of the the ticket bought
    assert tick == 1
  
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
    tick = t.buy_ticket("user@example.com", result[0][0], also_reserve_seats=True)
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

# def test_purchase_history_success(rdbms_connection, rdbms_admin_connection, neo4j_db):


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
#     user_mail = "user@example.com"
#     t.add_user(user_mail, None)
#     t.buy_ticket(user_mail, result[0][0], also_reserve_seats=True)
#     history = t.get_purchase_history(user_mail)
#     print(history)
#     #The ticket id of the the ticket bought
#     assert history == 1
  

def test_invalid_delete_user(rdbms_connection, rdbms_admin_connection, neo4j_db):
    t = Traits(rdbms_connection, rdbms_admin_connection, neo4j_db)
    # The user doesnt exist
    with pytest.raises(ValueError):
        t.delete_user("user2@example.com")

def test_add_train_without_permission(rdbms_connection, rdbms_admin_connection, neo4j_db):
    t = Traits(rdbms_connection, rdbms_connection, neo4j_db)
    # The permission is not there
    rec = t.add_train(TraitsKey('T2'), 50, TrainStatus.OPERATIONAL)
    assert rec == None

def test_update_train_details_failure(rdbms_connection, rdbms_admin_connection, neo4j_db):
    t = Traits(rdbms_connection, rdbms_admin_connection, neo4j_db)
    with pytest.raises(ValueError):
        t.update_train_details(TraitsKey('t3'), train_capacity = 10)

