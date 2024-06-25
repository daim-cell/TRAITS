from typing import List, Tuple, Optional, Dict
from traits.interface import TraitsUtilityInterface, TraitsInterface, TraitsKey, TrainStatus, SortingCriteria
from traits.interface import BASE_USER_NAME, BASE_USER_PASS, ADMIN_USER_NAME, ADMIN_USER_PASS
from datetime import datetime, date, time, timedelta
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
                date DATE NOT NULL,
                start_time TIME NOT NULL,
                end_time TIME NOT NULL,
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
            """CREATE TABLE IF NOT EXISTS Connections (
                connection_id INT PRIMARY KEY AUTO_INCREMENT,
                starting_station VARCHAR(255) NOT NULL,
                ending_station VARCHAR(255) NOT NULL,
                travel_time INT NOT NULL
            );""",
            """CREATE TABLE IF NOT EXISTS Schedules (
                schedule_id INT PRIMARY KEY AUTO_INCREMENT,
                train_id INT NOT NULL,
                starting_station_id INT NOT NULL,
                ending_station_id INT NOT NULL,
                start_time TIME NOT NULL,
                end_time TIME NOT NULL,
                valid_from DATE NOT NULL,
                valid_until DATE NOT NULL,
                FOREIGN KEY (train_id) REFERENCES Trains(train_id) ON DELETE CASCADE,
                FOREIGN KEY (starting_station_id) REFERENCES Stations(station_id) ON DELETE CASCADE,
                FOREIGN KEY (ending_station_id) REFERENCES Stations(station_id) ON DELETE CASCADE
            );""",
            # Views
            """ CREATE VIEW IF NOT EXISTS Purchase AS
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
            
            f"DROP USER IF EXISTS 'anonymous'@'%';",
            f"CREATE USER 'anonymous'@'%' IDENTIFIED BY '';"
            f"GRANT SELECT ON test.Trains TO 'anonymous'@'%';",
            f"GRANT SELECT ON test.Stations TO 'anonymous'@'%';",
            f"GRANT SELECT ON test.Trips TO 'anonymous'@'%';",
            
            f"DROP USER IF EXISTS '{BASE_USER_NAME}'@'%';",
            f"CREATE USER '{BASE_USER_NAME}'@'%' IDENTIFIED BY '{BASE_USER_PASS}';",
            f"GRANT SELECT ON test.Users TO '{BASE_USER_NAME}'@'%';",
            f"GRANT SELECT ON test.Schedules TO '{BASE_USER_NAME}'@'%';",
            f"GRANT SELECT, INSERT ON test.Tickets TO '{BASE_USER_NAME}'@'%';",
            f"GRANT SELECT, INSERT ON test.Reservations TO '{BASE_USER_NAME}'@'%';",
            f"GRANT SELECT, INSERT ON test.Purchase TO '{BASE_USER_NAME}'@'%';",
            f"GRANT SELECT ON test.Trains TO '{BASE_USER_NAME}'@'%';",
            f"GRANT SELECT ON test.Stations TO '{BASE_USER_NAME}'@'%';",
            f"GRANT SELECT ON test.Trips TO '{BASE_USER_NAME}'@'%';",

            f"DROP USER IF EXISTS '{ADMIN_USER_NAME}'@'%';",
            f"CREATE USER '{ADMIN_USER_NAME}'@'%' IDENTIFIED BY '{ADMIN_USER_PASS}';",
            f"GRANT ALL ON test.* TO '{ADMIN_USER_NAME}'@'%';",
            f"FLUSH PRIVILEGES;"

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
        cursor = self.rdbms_connection.cursor()
        cursor.execute("SELECT * FROM Schedules")
        schedules = cursor.fetchall()
        return schedules

    def _execute_neo4j_query(self, start_station, end_station, travel_time, is_departure_time, sort_by, is_ascending, limit):
        sort_criteria = ["overallTravelTime", "numberOfTrains","totalWaitingTime", "Price"]

        order_clause = "ASC" if is_ascending else "DESC"
        time_constraint = f"datetime(r.departure_time)  >= datetime('{travel_time}')" if is_departure_time else f"datetime(r.arrival_time <= '{travel_time}')"
        query = (f"""
                MATCH (start:Station {{name: '{start_station}'}}),(end:Station {{name: '{end_station}'}})
                MATCH path = (start)-[TRIP*]->(end)
                WHERE ALL(r in relationships(path) WHERE {time_constraint})
                WITH path, 
                    reduce(totalTravelTime = 0, r in relationships(path) | totalTravelTime + r.travel_time) AS overallTravelTime,
                    length(path) AS numberOfTrains,
                    duration.between(datetime('{travel_time}'), relationships(path)[0].departure_time).minutes AS initialWaitingTime,
                    reduce(waitingTime = 0, idx in range(0, length(path) - 2) |
                    waitingTime + duration.between(relationships(path)[idx].arrival_time, relationships(path)[idx + 1].departure_time).minutes) AS intWaitingTime, 
                    relationships(path)[0].departure_time AS firstDepartureTime
                WITH relationships(path) AS rels, overallTravelTime, numberOfTrains,initialWaitingTime, intWaitingTime,initialWaitingTime + intWaitingTime AS totalWaitingTime, firstDepartureTime
                WHERE ALL(r in relationships(path) WHERE date(r.departure_time) = date(firstDepartureTime))
                RETURN [r in rels | properties(r)] AS relations , overallTravelTime, numberOfTrains, totalWaitingTime,
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
        cursor = self.rdbms_connection.cursor()

        for route in routes:
            details = []
            for connect in route['relations']:
                cursor.execute("SELECT * FROM Trips WHERE trip_id = %s", (connect['trip_id'],))
                rec = cursor.fetchall()
                # return trip_ids only
                details.append(rec[0])
            detailed_routes.append(details)
        return detailed_routes
    
    def check_available_seats(self, trip_id: int) -> int:
        cursor = self.rdbms_admin_connection.cursor()
        
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

    def search_station_keys(self, starting_station_key: int|str, ending_station_key: int|str) -> None:
        """
        Check if the starting and ending station keys exist in the Stations table.
        Raise a ValueError if any of the keys do not exist.
        """

        if starting_station_key ==  ending_station_key:
            raise ValueError
        cursor = self.rdbms_connection.cursor()
        
        # Query to check if the starting station key exists
        cursor.execute("SELECT COUNT(*) FROM Stations WHERE name = %s", (starting_station_key,))
        start_station_count = cursor.fetchone()[0]
        
        # Query to check if the ending station key exists
        cursor.execute("SELECT COUNT(*) FROM Stations WHERE name = %s", (ending_station_key,))
        end_station_count = cursor.fetchone()[0]

        # Close the cursor
        cursor.close()
        
        # Raise ValueError if any of the keys do not exist
        if start_station_count == 0 or end_station_count == 0:
            raise ValueError
        
    def get_dates(self, valid_from_day: int, valid_from_month: int, valid_from_year: int,
                 valid_until_day: int, valid_until_month: int, valid_until_year: int) -> List[date]:
        cte_query = f"""
        WITH RECURSIVE DateRange AS (
            SELECT
                DATE(CONCAT({valid_from_year}, '-', {valid_from_month}, '-', {valid_from_day})) AS date
            UNION ALL
            SELECT
                DATE_ADD(date, INTERVAL 1 DAY)
            FROM
                DateRange
            WHERE
                date < DATE(CONCAT({valid_until_year}, '-', {valid_until_month}, '-', {valid_until_day}))
        )
        SELECT date FROM DateRange;
        """

        # Execute the CTE query
        cursor = self.rdbms_admin_connection.cursor()
        cursor.execute(cte_query)
        dates = cursor.fetchall()
        return dates
    
    def add_travel_time(self, starting_hours_24_h: int, starting_minutes: int, travel_minutes: int) -> str:
    # Create start time object
        start_time = time(hour=starting_hours_24_h, minute=starting_minutes)

        # Create travel time delta
        travel_time = timedelta(minutes=travel_minutes)

        # Combine start date and time, then add the travel time
        start_datetime = datetime.combine(datetime.today(), start_time)  # Important step
        end_datetime = start_datetime + travel_time

        # Format the end time as a string
        end_time = end_datetime.time().strftime("%H:%M:%S")
        end_hours = end_datetime.time().hour
        end_minutes = end_datetime.time().minute
        return end_time, end_hours, end_minutes
    
    def is_schedule_feasible(self, train_id: int, start_time: time, end_time: time, valid_from: date, valid_until: date) -> bool:
        # Check if a train is already scheduled during this time
        cursor = self.rdbms_connection.cursor()
        new_start_time = timedelta(hours=int(start_time.split(':')[0]), 
                           minutes=int(start_time.split(':')[1]), 
                           seconds=int(start_time.split(':')[2]))
        new_end_time = timedelta(hours=int(end_time.split(':')[0]), 
                         minutes=int(end_time.split(':')[1]), 
                         seconds=int(end_time.split(':')[2]))
        
        # The schedule went onto the next day
        if (new_end_time<new_start_time):
            return False
        cursor.execute(
            """
            SELECT start_time, end_time FROM Schedules
            WHERE train_id = %s
            AND (
                (%s BETWEEN valid_from AND valid_until OR %s BETWEEN valid_from AND valid_until)
                OR
                (valid_from BETWEEN %s AND %s OR valid_until BETWEEN %s AND %s)
            );
            """, (train_id, valid_from, valid_until, valid_from, valid_until, valid_from, valid_until)
        )
        same_day_schedules = cursor.fetchall()
        
        
        if same_day_schedules:
            for sch in same_day_schedules:
                if (new_start_time <= sch[1]  and new_end_time >= sch[0]):
            # if overlapping_schedules > 0:
                    return False
        

        prev_date = datetime.strptime(valid_from, "%Y-%m-%d") - timedelta(days=1)
        # Ensure at least 6 hours before next day's first start
        cursor.execute(
            """
            SELECT end_time FROM Schedules 
            WHERE train_id = %s AND  (%s BETWEEN valid_from AND valid_until)
            ORDER BY end_time DESC LIMIT 1;
            """, (train_id, prev_date,)
        )
        # If new schedule is within six hours of previous day
        last_end_time = cursor.fetchone()
        if last_end_time:
            if (last_end_time[0] - new_start_time).total_seconds() > 64800:
                return False
            
        next_date = datetime.strptime(valid_from, "%Y-%m-%d") + timedelta(days=1)
        # Ensure at least 6 hours before next day's first start
        cursor.execute(
            """
            SELECT end_time FROM Schedules 
            WHERE train_id = %s AND  (%s BETWEEN valid_from AND valid_until)
            ORDER BY start_time ASC LIMIT 1;
            """, (train_id, next_date,)
        )
        # If new schedule is within six hours of previous day
        first_start_time = cursor.fetchone()
        if first_start_time:
            if (new_end_time - first_start_time[0]).total_seconds() > 64800:
                return False

        return True
    
    def add_schedule(self, train_id: int, start_station_id: int, end_station_id: int, start_time: time, end_time: time, valid_from: date, valid_until: date) -> None:
        
        # start_time = datetime.strptime(start_time, '%H:%M:%S')
        # end_time = datetime.strptime(end_time, '%H:%M:%S')
        if not self.is_schedule_feasible(train_id, start_time, end_time, valid_from, valid_until):
            raise ValueError

        cursor = self.rdbms_admin_connection.cursor()
        cursor.execute(
            """
            INSERT INTO Schedules (train_id, starting_station_id, ending_station_id, start_time, end_time, valid_from, valid_until)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, (train_id, start_station_id, end_station_id, start_time, end_time, valid_from, valid_until)
        )
        self.rdbms_admin_connection.commit()


    
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
        travel_time = date(travel_time_year, travel_time_month, travel_time_day) if travel_time_day or travel_time_month or travel_time_year else datetime.now()
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
        # This is a problem why normal user can get status of a train
        cursor = self.rdbms_connection.cursor()
        cursor.execute("SELECT t.status FROM Trains t WHERE t.train_name = %s;", (train_key.to_string(),))
        status = cursor.fetchone()
        if status is not None:
            return TrainStatus(status[0])
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
            raise ValueError


        # Insert into Tickets table
        cursor.execute(
            "INSERT INTO Tickets (user_id, trip_id, reserved_seat) VALUES (%s, %s, %s);",
            (user[0], connection[0], also_reserve_seats)
        )
        ticket_id = cursor.lastrowid

        if also_reserve_seats:
            # Check available seats
            available_seats = self.utility.check_available_seats(connection[0])
            if available_seats > 0:
                # Insert into Reservations table
                cursor.execute(
                    "INSERT INTO Reservations (ticket_id) VALUES (%s);", (ticket_id,)
                )
            else:
                raise ValueError

        self.rdbms_connection.commit()
        return cursor.lastrowid

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
        cursor.execute("SELECT COUNT(*) FROM Users WHERE email = %s;", (user_email,))
        if cursor.fetchone()[0] == 0:
            raise ValueError
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
            
            rec = cursor.execute(insert_train_query, (train_key.to_string(),  train_capacity, train_status.value))

            self.rdbms_admin_connection.commit()
            return rec
        except Exception as ex:
            raise ValueError
        
    def update_train_details(self, train_key: TraitsKey, train_capacity: Optional[int] = None, train_status: Optional[TrainStatus] = None) -> None:
        """
        Update the details of existing train if specified (i.e., not None), otherwise do nothing.
        """
        # Implementation here
        cursor = self.rdbms_admin_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM Trains WHERE train_name = %s;", (train_key.to_string(),))

        if cursor.fetchone()[0] == 0:
            raise ValueError
        try:
            if train_capacity is not None:
                update_capacity_query = """
                UPDATE Trains SET capacity = %s WHERE train_name = %s;
                """
                cursor.execute(update_capacity_query, (train_capacity, train_key.to_string(),))
            
            if train_status is not None:
                update_status_query = """
                UPDATE Trains SET status = %s WHERE train_name = %s;
                """
                cursor.execute(update_status_query, (train_status.value, train_key.to_string(),))
            
            
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

            # Insert the station as a node in Neo4j
            with self.neo4j_driver.session() as session:
                create_node_query = """
                CREATE (s:Station {name: $name, details: $details})
                """
                session.run(create_node_query, name=train_station_key.to_string(), details=train_station_details)
        
        except Exception as e:
            self.rdbms_admin_connection.rollback()
            raise ValueError
        finally:
            cursor.close()
    
    def connect_train_stations(self, starting_train_station_key: TraitsKey, ending_train_station_key: TraitsKey, travel_time_in_minutes: int)  -> None:
        """
        Connect to train station so trains can travel on them
        """
        # Implementation here
        
        try:
            self.utility.search_station_keys(starting_train_station_key.to_string(), ending_train_station_key.to_string())

            if travel_time_in_minutes < 1 or travel_time_in_minutes > 60:
                raise ValueError 
            # Create a relationship between the stations
            cursor = self.rdbms_admin_connection.cursor()
     
            # Check if station already exists
            check_station_query = "SELECT COUNT(*) FROM Connections WHERE starting_station = %s AND ending_station = %s"
            cursor.execute(check_station_query, (starting_train_station_key.to_string(), ending_train_station_key.to_string()))
            if cursor.fetchone()[0] > 0:
                raise ValueError

            # Insert the station if it doesn't exist
            insert_station_query = "INSERT INTO Connections (starting_station, ending_station, travel_time) VALUES (%s, %s, %s)"
            cursor.execute(insert_station_query, (starting_train_station_key.to_string(), ending_train_station_key.to_string(), travel_time_in_minutes))
            # For the other way around
            cursor.execute(insert_station_query, (ending_train_station_key.to_string(), starting_train_station_key.to_string(), travel_time_in_minutes))
            
            self.rdbms_admin_connection.commit()
        except Exception as e:
            raise e

    def add_schedule(self, train_key: TraitsKey,
                 starting_hours_24_h: int, starting_minutes: int,
                 stops: List[Tuple[TraitsKey, int]], # [station_key, waiting_time]
                 valid_from_day: int, valid_from_month: int, valid_from_year: int,
                 valid_until_day: int, valid_until_month: int, valid_until_year: int) -> None:
        """
        Create a schedule for a given train.
        """
        cursor = self.rdbms_admin_connection.cursor()
        try:
            # Check if train exists
            check_train_query = "SELECT train_id FROM Trains WHERE train_name = %s"
            cursor.execute(check_train_query, (train_key.to_string(),))
            train_id = cursor.fetchone()
            if not train_id:
                raise ValueError

            train_id = train_id[0]
            # Ensure stops are valid and fetch their IDs
            stop_info = []
            start_time = f"{starting_hours_24_h}:{starting_minutes}:00"
            hrs = starting_hours_24_h
            mins = starting_minutes
            for i, (stop_key, waiting_time) in enumerate(stops):
                cursor.execute("SELECT station_id FROM Stations WHERE name = %s", (stop_key.to_string(),))
                station_id = cursor.fetchone()
                if not station_id:
                    raise ValueError
                if i != 0:
                    cursor.execute("SELECT travel_time FROM Connections WHERE starting_station = %s AND ending_station = %s", ( prev_station_name.to_string(),stop_key.to_string(),))
                    travel_time = cursor.fetchone()
                    if not travel_time:
                        raise ValueError
                    end_time, hrs, mins = self.utility.add_travel_time(hrs , mins, travel_time[0])
                    stop_info.append([prev_station_id, station_id[0], start_time, end_time, prev_station_name.to_string(),stop_key.to_string(), travel_time[0]])
                    start_time, hrs, mins = self.utility.add_travel_time(hrs , mins, waiting_time)
                # Last stop to have atleast 10 minute waiting time
                if i == len(stops)-1 and waiting_time < 10:
                    raise ValueError
                prev_station_id = station_id[0]
                prev_station_name = stop_key
                
            # Validate time and date ranges
            if starting_hours_24_h < 0 or starting_hours_24_h > 23 or starting_minutes < 0 or starting_minutes > 59:
                raise ValueError
            
            valid_from = f"{valid_from_year}-{valid_from_month:02d}-{valid_from_day:02d}"
            valid_until = f"{valid_until_year}-{valid_until_month:02d}-{valid_until_day:02d}"
            self.utility.add_schedule(train_id, stop_info[0][0], stop_info[-1][1],f"{starting_hours_24_h}:{starting_minutes}:00", stop_info[-1][3], valid_from, valid_until )
            dates = self.utility.get_dates(valid_from_day, valid_from_month, valid_from_year,
                 valid_until_day, valid_until_month, valid_until_year)
            insert_trip_query = "INSERT INTO Trips (train_id, starting_station_id, ending_station_id, date, start_time, end_time) VALUES (%s,%s,%s,%s,%s,%s)"
            with self.neo4j_driver.session() as session:
                for ind_date in dates:
                    
                    for stop in stop_info:
                        cursor.execute(insert_trip_query,(train_id, stop[0], stop[1], ind_date[0], stop[2], stop[3]) )
                        query = """
                        MATCH (a:Station {name: $start_station_name}), (b:Station {name: $end_station_name})
                        CREATE (a)-[:TRIP {trip_id: $trip_id, departure_time: $departure_time, travel_time: $travel_time, arrival_time: $arrival_time, train_name: $train_name}]->(b)
                        """
                        time_object1 = datetime.strptime(stop[2], '%H:%M:%S').time()
                        dep_object = datetime.combine(ind_date[0], time_object1)
                        time_object2 = datetime.strptime(stop[3], '%H:%M:%S').time()
                        arr_object = datetime.combine(ind_date[0], time_object2)
                        session.run(query, trip_id=cursor.lastrowid,start_station_name=stop[4], end_station_name=stop[5], departure_time=dep_object, travel_time=stop[6], arrival_time=arr_object, train_name=train_key.to_string())


            # Insert the schedule into the database
            self.rdbms_admin_connection.commit()
        except Exception as e:
            self.rdbms_admin_connection.rollback()
            raise e
        finally:
            cursor.close()
