from typing import List, Tuple, Optional, Dict
from traits.interface import TraitsUtilityInterface, TraitsInterface, TraitsKey, TrainStatus, SortingCriteria
from traits.interface import BASE_USER_NAME, BASE_USER_PASS, ADMIN_USER_NAME, ADMIN_USER_PASS
from datetime import datetime
class TraitsUtility(TraitsUtilityInterface):
    def __init__(self, rdbms_connection, rdbms_admin_connection, neo4j_driver) -> None:
        self.rdbms_connection = rdbms_connection
        self.rdbms_admin_connection = rdbms_admin_connection
        self.neo4j_driver = neo4j_driver

    def generate_sql_initialization_code() -> List[str]:
        """
        Returns a list of string each one containing a SQL statement to setup the database.
        """
        # Implementation here

        return [
            """ CREATE TABLE IF NOT EXISTS Trains (
                train_id INT PRIMARY KEY,
                train_name VARCHAR(255) NOT NULL,
                capacity INT NOT NULL,
                status VARCHAR(255) NOT NULL
            );""",
            """ CREATE TABLE IF NOT EXISTS Stations (
                station_id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL
            );""",
            """ CREATE TABLE IF NOT EXISTS Trips (
                trip_id INT PRIMARY KEY,
                train_id INT NOT NULL,
                starting_station_id INT NOT NULL,
                ending_station_id INT NOT NULL,
                start_time DATETIME NOT NULL,
                end_time DATETIME NOT NULL,
                FOREIGN KEY (train_id) REFERENCES Trains(train_id),
                FOREIGN KEY (starting_station_id) REFERENCES Stations(station_id),
                FOREIGN KEY (ending_station_id) REFERENCES Stations(station_id)
            );""",
            f"DROP USER IF EXISTS '{ADMIN_USER_NAME}'@'%';",
            f"DROP USER IF EXISTS '{BASE_USER_NAME}'@'%';",
            f"CREATE USER '{ADMIN_USER_NAME}'@'%' IDENTIFIED BY '{ADMIN_USER_PASS}';",
            f"CREATE USER '{BASE_USER_NAME}'@'%' IDENTIFIED BY '{BASE_USER_PASS}';",
            f"GRANT ALL PRIVILEGES ON test.* TO '{ADMIN_USER_NAME}'@'%';"
            f"GRANT SELECT, INSERT, UPDATE ON test.* TO '{BASE_USER_NAME}'@'%';"

        ]

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
    def __init__(self, rdbms_connection, rdbms_admin_connection, neo4j_driver) -> None:
        self.rdbms_connection = rdbms_connection
        self.rdbms_admin_connection = rdbms_admin_connection
        self.neo4j_driver = neo4j_driver

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
        if starting_station_key.to_string() == ending_station_key.to_string():
            raise ValueError
        
        travel_time = datetime(travel_time_year, travel_time_month, travel_time_day) if travel_time_day or travel_time_month or travel_time_year else datetime.now()
        travel_time_str = travel_time.strftime('%Y-%m-%dT%H:%M:%S')

         # Build the Neo4j query
        routes = self._execute_neo4j_query(starting_station_key.to_string(), ending_station_key.to_string(), travel_time_str, is_departure_time, sort_by, is_ascending, limit)
        if len(routes) == 0:
            raise ValueError
        # Fetch additional details from MariaDB
        detailed_routes = self._fetch_details_from_mariadb(routes)

        return detailed_routes
    
    def _execute_neo4j_query(self, start_station, end_station, travel_time, is_departure_time, sort_by, is_ascending, limit):
        sort_criteria = {
            SortingCriteria.OVERALL_TRAVEL_TIME: "overallTravelTime",
            SortingCriteria.NUMBER_OF_TRAIN_CHANGES: "numberOfTrains",
            SortingCriteria.OVERALL_WAITING_TIME: "totalWaitingTime",
            SortingCriteria.ESTIMATED_PRICE: "Price"
        }

        order_clause = "ASC" if is_ascending else "DESC"
        time_constraint = f"r.departure_time  >= '{travel_time}'" if is_departure_time else f"r.arrival_time <= '{travel_time}'"
        query = (f"""MATCH (start:Station {{name: '{start_station}'}})
                MATCH (end:Station {{name: '{end_station}'}})
                MATCH path = (start)-[TRIP*]->(end)
                WHERE ALL(r in relationships(path) WHERE {time_constraint})
                WITH path, 
                    reduce(totalTravelTime = 0, r in relationships(path) | totalTravelTime + r.travel_time) AS overallTravelTime,
                    length(path) AS numberOfTrains,
                    duration.between('{travel_time}', relationships(path)[0].departure_time).minutes AS initialWaitingTime,
                    reduce(waitingTime = 0, idx in range(0, length(path) - 2) |
                waitingTime + duration.between(relationships(path)[idx].arrival_time, relationships(path)[idx + 1].departure_time).minutes) AS intWaitingTime
                WITH path, overallTravelTime, numberOfTrains,initialWaitingTime, intWaitingTime,initialWaitingTime + intWaitingTime AS totalWaitingTime
                RETURN path, overallTravelTime, numberOfTrains, totalWaitingTime,
                    (overallTravelTime - intWaitingTime) / 2 + (numberOfTrains * 2) AS Price
                ORDER BY {sort_criteria[sort_by]} {order_clause} 
                LIMIT {limit}
""")    
        
        with self.neo4j_driver.session() as session:
            result = session.run(query)
            routes = [record.data() for record in result]
        return routes


        

    def _fetch_details_from_mariadb(self, routes):
        detailed_routes = []
        for route in routes:
            details = []
            for rel in route.relationships:
                trip_id = rel['relationship']['properties']['trip_id']
                self.rdbms_admin_connection.execute("SELECT * FROM Trips WHERE trip_id = ?", (trip_id,))
                details.extend(self.rdbms_connection.fetchall())
            detailed_routes.append(details)
        return detailed_routes
    
    def get_train_current_status(self, train_key: TraitsKey) -> Optional[TrainStatus]:
        """
        Check the status of a train. If the train does not exist returns None
        """
        # Implementation here
        cursor = self.rdbms_connection.cursor()
        cursor.execute("SELECT t.status FROM Trains t WHERE t.train_name = %s", (train_key.to_string(),))
        status = cursor.fetchone()
        if status is not None:
            return status
        return None

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
        try:
            cursor = self.rdbms_admin_connection.cursor()
            insert_train_query = """
            INSERT INTO Trains (train_name, capacity, status)
            VALUES (%s, %s, %s)
            """
            cursor.execute(insert_train_query, ( train_key.to_string(),  train_capacity,train_status.OPERATIONAL))
            cursor.commit()
            return True
        except:
            return False
        
        

    def update_train_details(self, train_key: TraitsKey, train_capacity: Optional[int] = None, train_status: Optional[TrainStatus] = None) -> None:
        """
        Update the details of existing train if specified (i.e., not None), otherwise do nothing.
        """
        # Implementation here
        cursor = self.rdbms_admin_connection.cursor()
        if train_capacity is not None:
            update_capacity_query = """
            UPDATE Trains SET capacity = %s WHERE train_id = %s
            """
            cursor.execute(update_capacity_query, (train_capacity, train_key))
        
        if train_status is not None:
            update_status_query = """
            UPDATE Trains SET status = %s WHERE train_id = %s
            """
            cursor.execute(update_status_query, (train_status, train_key))

        cursor.commit()
        
        

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