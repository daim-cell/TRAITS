from typing import List, Tuple, Optional, Dict
from traits.interface import TraitsUtilityInterface, TraitsInterface, TraitsKey, TrainStatus, SortingCriteria

class TraitsUtility(TraitsUtilityInterface):
    def __init__(self, rdbms_connection, rdbms_admin_connection, neo4j_driver) -> None:
        self.rdbms_connection = rdbms_connection
        self.rdbms_admin_connection = rdbms_admin_connection
        self.neo4j_driver = neo4j_driver

    def generate_sql_initialization_code(self) -> List[str]:
        """
        Returns a list of string each one containing a SQL statement to setup the database.
        """
        # Implementation here
        pass

    def get_all_users(self) -> List:
        """
        Return all the users stored in the database
        """
        # Implementation here
        pass

    def get_all_schedules(self) -> List:
        """
        Return all the schedules stored in the database
        """
        # Implementation here
        pass


class Traits(TraitsInterface):
    def search_connections(self, starting_station_key: TraitsKey, ending_station_key: TraitsKey,
                           travel_time_day: int = None, travel_time_month : int = None, travel_time_year : int = None,
                           is_departure_time=True,
                           sort_by : SortingCriteria = SortingCriteria.OVERALL_TRAVEL_TIME, is_ascending : bool =True,
                           limit : int = 5) -> List:
        """
        Search Train Connections (between two stations).
        Sorting criteria can be one of the following:overall travel time, number of train changes, waiting time, and estimated price

        Return the connections from a starting and ending stations, possibly including changes at interchanging stations.
        Returns an empty list if no connections are possible
        Raise a ValueError in case of errors and if the starting or ending stations are the same
        """
        # Implementation here
        pass

    def get_train_current_status(self, train_key: TraitsKey) -> Optional[TrainStatus]:
        """
        Check the status of a train. If the train does not exist returns None
        """
        # Implementation here
        pass

    def buy_ticket(self, user_email: str, connection, also_reserve_seats=True):
        """
        Given a train connection instance (e.g., on a given date/time), registered users can book tickets and optionally reserve seats.
        """
        # Implementation here
        pass

    def get_purchase_history(self, user_email: str) -> List:
        """
        Access Purchase History
        """
        # Implementation here
        pass

    def add_user(self, user_email: str, user_details) -> None:
        """
        Add a new user to the system with given email and details.
        """
        # Implementation here
        pass

    def delete_user(self, user_email: str) -> None:
        """
        Delete the user from the db if the user exists.
        """
        # Implementation here
        pass

    def add_train(self, train_key: TraitsKey, train_capacity: int, train_status: TrainStatus) -> None:
        """
        Add new trains to the system with given code.
        """
        # Implementation here
        pass

    def update_train_details(self, train_key: TraitsKey, train_capacity: Optional[int] = None, train_status: Optional[TrainStatus] = None) -> None:
        """
        Update the details of existing train if specified (i.e., not None), otherwise do nothing.
        """
        # Implementation here
        pass

    def delete_train(self, train_key: TraitsKey) -> None:
        """
        Drop the train from the system. Note that all its schedules, reservations, etc. must be also dropped.
        """
        # Implementation here
        pass

    def add_train_station(self, train_station_key: TraitsKey, train_station_details) -> None:
        """
        Add a train station
        """
        # Implementation here
        pass
    
    def connect_train_stations(self, starting_train_station_key: TraitsKey, ending_train_station_key: TraitsKey, travel_time_in_minutes: int)  -> None:
        """
        Connect to train station so trains can travel on them
        """
        # Implementation here
        pass

    def add_schedule(self, train_key: TraitsKey,
                     starting_hours_24_h: int, starting_minutes: int,
                     stops: List[Tuple[TraitsKey, int]], # [station_key, waiting_time]
                     valid_from_day: int, valid_from_month: int, valid_from_year: int,
                     valid_until_day: int, valid_until_month: int, valid_until_year: int) -> None:
        """
        Create a schedule for a give train.
        """
        # Implementation here
        pass