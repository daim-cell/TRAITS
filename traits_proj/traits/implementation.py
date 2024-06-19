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
            """CREATE TABLE IF NOT EXISTS Users (
                user_id INT PRIMARY KEY AUTO_INCREMENT,
                details VARCHAR(255) DEFAULT NULL,
                email VARCHAR(255) NOT NULL UNIQUE CHECK (email REGEXP '^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
            );"""
            """ CREATE TABLE IF NOT EXISTS Trains (
                train_id INT PRIMARY KEY AUTO_INCREMENT,
                train_name VARCHAR(255) NOT NULL UNIQUE,
                capacity INT NOT NULL,
                status INT NOT NULL
            );""",
            """ CREATE TABLE IF NOT EXISTS Stations (
                station_id INTEGER PRIMARY KEY AUTO_INCREMENT,
                name TEXT UNIQUE NOT NULL
            );""",
            """ CREATE TABLE IF NOT EXISTS Trips (
                trip_id INT PRIMARY KEY AUTO_INCREMENT,
                train_id INT NOT NULL,
                starting_station_id INT NOT NULL,
                ending_station_id INT NOT NULL,
                start_time DATETIME NOT NULL,
                end_time DATETIME NOT NULL,
                FOREIGN KEY (train_id) REFERENCES Trains(train_id) ON DELETE CASCADE,
                FOREIGN KEY (starting_station_id) REFERENCES Stations(station_id),
                FOREIGN KEY (ending_station_id) REFERENCES Stations(station_id)
            );""",
            """CREATE TABLE IF NOT EXISTS Tickets (
                ticket_id INT PRIMARY KEY AUTO_INCREMENT,
                user_id INT NOT NULL,
                trip_id INT NOT NULL,
                booking_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                reserved_seat BOOLEAN NOT NULL DEFAULT FALSE,
                price INT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (trip_id) REFERENCES Trips(trip_id) ON DELETE CASCADE
            );""",
            """CREATE TABLE IF NOT EXISTS Reservations (
                reservation_id INT PRIMARY KEY AUTO_INCREMENT,
                ticket_id INT NOT NULL,
                FOREIGN KEY (ticket_id) REFERENCES Tickets(ticket_id) ON DELETE CASCADE
            );""",
            # Views
            """ CREATE VIEW Purchase AS
                SELECT
                    tk.booking_time AS purchase_time,
                    tk.ticket_id, u.email AS user_email,
                    s1.name AS starting_station_name, s2.name AS ending_station_name,
                    tr.start_time, tr.end_time,
                    tk.price AS connection_price,
                    tk.reserved_seat
                FROM
                    Tickets tk
                    JOIN Trips tr ON tk.trip_id = tr.trip_id
                    JOIN Stations s1 ON tr.starting_station_id = s1.station_id
                    JOIN Stations s2 ON tr.ending_station_id = s2.station_id
                    JOIN Users u ON tk.user_id = u.user_id;""",
            # Triggers
            """
            CREATE TRIGGER calculate_total_price_before_insert
            BEFORE INSERT ON Tickets
            FOR EACH ROW
            BEGIN
                DECLARE start_time DATETIME;
                DECLARE end_time DATETIME;
                DECLARE minutes_diff INT;
                SELECT t.start_time, t.end_time
                INTO start_time, end_time
                FROM Trips t
                WHERE t.trip_id = NEW.trip_id;
                SET minutes_diff = TIMESTAMPDIFF(MINUTE, start_time, end_time);
                SET NEW.price = (minutes_diff / 2) + 2;
            END;""",
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
        cursor = self.rdbms_admin_connection.cursor()
        cursor.execute("SELECT * FROM Users")
        users = cursor.fetchall()
        return users
        

    def get_all_schedules(self) -> List:
        """
        Return all the schedules stored in the database
        """
        # Implementation here
        pass

    def _execute_neo4j_query(self, start_station, end_station, travel_time, is_departure_time, sort_by, is_ascending, limit):
        sort_criteria = ["overallTravelTime", "numberOfTrains","totalWaitingTime", "Price"]

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
                ORDER BY {sort_criteria[sort_by.value]} {order_clause} 
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
                self.rdbms_admin_connection.execute("SELECT * FROM Trips WHERE trip_id = ?;", (trip_id,))
                details.extend(self.rdbms_connection.fetchall())
            detailed_routes.append(details)
        return detailed_routes
    
    def check_available_seats(self, trip_id: int) -> int:
        cursor = self.rdbms_connection.cursor()
        
        # Fetch the train_id for the given trip_id
        cursor.execute("SELECT train_id FROM Trips WHERE trip_id = %s;", (trip_id,))
        train_id = cursor.fetchone()
        if not train_id:
            raise ValueError("Trip does not exist")
        
        train_id = train_id[0]

        # Fetch the train capacity
        cursor.execute("SELECT capacity FROM Trains WHERE train_id = %s;", (train_id,))
        train_capacity = cursor.fetchone()
        if not train_capacity:
            raise ValueError("Train does not exist")

        train_capacity = train_capacity[0]

        # Fetch the number of reserved seats for the given trip_id
        cursor.execute(
            """
            SELECT COUNT(*) FROM Reservations R
            JOIN Tickets T ON R.ticket_id = T.ticket_id
            WHERE T.trip_id = %s;
            """,
            (trip_id,)
        )
        reserved_seats = cursor.fetchone()[0]

        available_seats = train_capacity - reserved_seats
        return available_seats

    def search_station_keys(self, starting_station_key: int, ending_station_key: int) -> None:
        """
        Check if the starting and ending station keys exist in the Stations table.
        Raise a ValueError if any of the keys do not exist.
        """
        cursor = self.rdbms_connection.cursor()
        
        # Query to check if the starting station key exists
        cursor.execute("SELECT COUNT(*) FROM Stations WHERE station_id = %s", (starting_station_key,))
        start_station_count = cursor.fetchone()[0]
        
        # Query to check if the ending station key exists
        cursor.execute("SELECT COUNT(*) FROM Stations WHERE station_id = %s", (ending_station_key,))
        end_station_count = cursor.fetchone()[0]

        # Close the cursor
        cursor.close()
        
        # Raise ValueError if any of the keys do not exist
        if start_station_count == 0 or end_station_count == 0:
            raise ValueError
        

    
class Traits(TraitsInterface):
    def __init__(self, rdbms_connection, rdbms_admin_connection, neo4j_driver) -> None:
        self.rdbms_connection = rdbms_connection
        self.rdbms_admin_connection = rdbms_admin_connection
        self.neo4j_driver = neo4j_driver
        self.utility = TraitsUtility(rdbms_connection, rdbms_admin_connection, neo4j_driver)

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
        self.utility.search_station_keys(starting_station_key.to_string(), ending_station_key.to_string())
        travel_time = datetime(travel_time_year, travel_time_month, travel_time_day) if travel_time_day or travel_time_month or travel_time_year else datetime.now()
        travel_time_str = travel_time.strftime('%Y-%m-%dT%H:%M:%S')

         # Build the Neo4j query
        routes = self.utility._execute_neo4j_query(starting_station_key.to_string(), ending_station_key.to_string(), travel_time_str, is_departure_time, sort_by, is_ascending, limit)
        if len(routes) == 0:
            return []
        # Fetch additional details from MariaDB
        detailed_routes = self.utility._fetch_details_from_mariadb(routes)

        return detailed_routes
    
    def get_train_current_status(self, train_key: TraitsKey) -> Optional[TrainStatus]:
        """
        Check the status of a train. If the train does not exist returns None
        """
        # Implementation here
        cursor = self.rdbms_connection.cursor()
        cursor.execute("SELECT t.status FROM Trains t WHERE t.train_name = %s;", (train_key.to_string(),))
        status = cursor.fetchone()
        if status is not None:
            return status[0]
        return None

    def buy_ticket(self, user_email: str, connection, also_reserve_seats=True):
        """
        Given a train connection instance (e.g., on a given date/time), registered users can book tickets and optionally reserve seats.
        """
        # Implementation here
        cursor = self.rdbms_connection.cursor()
        # Assuming the connection parameter is a trip object
        # Fetch trip details and calculate the total price
        cursor.execute("SELECT * FROM Users WHERE email = %s;", (user_email,))
        user = cursor.fetchone()
        if not user:
            raise ValueError("User does not exist")


        # Insert into Tickets table
        cursor.execute(
            "INSERT INTO Tickets (user_id, trip_id, reserved_seat) VALUES (%s, %s, %s);",
            (user.user_id, connection.trip_id, also_reserve_seats)
        )
        ticket_id = cursor.lastrowid

        if also_reserve_seats:
            # Check available seats
            available_seats = self.utility.check_available_seats(connection.trip_id)
            if available_seats > 0:
                # Insert into Reservations table
                cursor.execute(
                    "INSERT INTO Reservations (ticket_id) VALUES (%s);", (ticket_id,)
                )
            else:
                raise ValueError('No Seats to reserve')

        self.rdbms_connection.commit()

    def get_purchase_history(self, user_email: str) -> List:
        """
        Access Purchase History
        """
        cursor = self.rdbms_connection.cursor()
        # Implementation here
        cursor.execute("SELECT * FROM Users WHERE email = %s;", (user_email,))
        user = cursor.fetchone()
        if not user:
            return []
        cursor = self.rdbms_connection.cursor()
        cursor.execute("""SELECT *
                        FROM Purchase
                        WHERE user_email = %s
                        ORDER BY purchase_time DESC;
                        """, (user_email,))
        records = cursor.fetchall()
        return records

    def add_user(self, user_email: str, user_details) -> None:
        """
        Add a new user to the system with given email and details.
        """
        # Implementation here
        cursor = self.rdbms_admin_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM Users WHERE email = %s;", (user_email,))
        if cursor.fetchone()[0] > 0:
            raise ValueError
        try:
            cursor.execute("INSERT INTO Users (email, details) VALUES (%s, %s);", (user_email, user_details))
        except:
            raise ValueError
        self.rdbms_admin_connection.commit()

    def delete_user(self, user_email: str) -> None:
        """
        Delete the user from the db if the user exists.
        """
        cursor = self.rdbms_admin_connection.cursor()
        # Implementation here
        cursor.execute("DELETE FROM Users WHERE email = %s;", (user_email,))
        # The data should delete itself on the basis of cascade
        self.rdbms_admin_connection.commit()

    def add_train(self, train_key: TraitsKey, train_capacity: int, train_status: TrainStatus) -> None:
        """
        Add new trains to the system with given code.
        """
        # Implementation here
        try:
            cursor = self.rdbms_admin_connection.cursor()
            insert_train_query = """
            INSERT INTO Trains (train_name, capacity, status)
            VALUES (%s, %s, %s);
            """
            
            cursor.execute(insert_train_query, ( train_key.to_string(),  train_capacity, train_status.value))
           
            self.rdbms_admin_connection.commit()
            
        except Exception as ex:
            
            raise ValueError
        
        

    def update_train_details(self, train_key: TraitsKey, train_capacity: Optional[int] = None, train_status: Optional[TrainStatus] = None) -> None:
        """
        Update the details of existing train if specified (i.e., not None), otherwise do nothing.
        """
        # Implementation here
        cursor = self.rdbms_admin_connection.cursor()
        try:
            if train_capacity is not None:
                update_capacity_query = """
                UPDATE Trains SET capacity = %s WHERE train_name = %s;
                """
                cursor.execute(update_capacity_query, (train_capacity, train_key.to_string()))
            
            if train_status is not None:
                update_status_query = """
                UPDATE Trains SET status = %s WHERE train_name = %s;
                """
                print('update', train_status.value, train_key.to_string())
                cursor.execute(update_status_query, (train_status.value, train_key.to_string()))
            
            
            self.rdbms_admin_connection.commit()
        except Exception as Ex:
            raise Ex
        
        

    def delete_train(self, train_key: TraitsKey) -> None:
        """
        Drop the train from the system. Note that all its schedules, reservations, etc. must be also dropped.
        """
        # Implementation here
        cursor = self.rdbms_admin_connection.cursor()
        try:
            # Delete the train and all related records (assuming cascading deletes are set up)
            delete_train_query = "DELETE FROM Trains WHERE train_name = %s"
            cursor.execute(delete_train_query, (train_key.to_string(),))
            self.rdbms_admin_connection.commit()
        except Exception as e:
            self.rdbms_admin_connection.rollback()
            raise e
        finally:
            cursor.close()

    def add_train_station(self, train_station_key: TraitsKey, train_station_details) -> None:
        """
        Add a train station
        """
        # Implementation here
        cursor = self.rdbms_admin_connection.cursor()
        try:
            # Check if station already exists
            check_station_query = "SELECT COUNT(*) FROM Stations WHERE name = %s"
            cursor.execute(check_station_query, (train_station_key.to_string(),))
            if cursor.fetchone()[0] > 0:
                raise ValueError

            # Insert the station if it doesn't exist
            insert_station_query = "INSERT INTO Stations (name) VALUES (%s)"
            cursor.execute(insert_station_query, (train_station_key.to_string(),))
            self.rdbms_admin_connection.commit()
        except Exception as e:
            self.rdbms_admin_connection.rollback()
            raise e
        finally:
            cursor.close()
    
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