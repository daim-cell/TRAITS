from traits.implementation import Traits, TraitsUtility
from traits.interface import TraitsKey, TrainStatus, SortingCriteria
import pytest


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

def test_search_connections_same_station(rdbms_connection, rdbms_admin_connection, neo4j_db):
    t = Traits(rdbms_connection, rdbms_admin_connection, neo4j_db)

    starting_station_key = TraitsKey("1")
    ending_station_key = TraitsKey("1")

    with pytest.raises(ValueError):
        t.search_connections(starting_station_key, ending_station_key)
