# Description


To pass the assignment, you need the following:

1. A working solution that **passes all the public tests** and **passes all your personal tests**

    >> NOTE: Failing to pass all the public and personal tests will result in a strong penalty (50/100) even if your solution passes **some** tests and implements the right functionalities.

2. A succinct description of your solution containing a **motivation** for each major design decision. Examples include but are not limited to:
    - *Where did you use NoSQL/SQL and why?*
    - *What is the schema of your Relational DB? How did you obtain it?*
    - *How did you approach the solution?*
    - *How did you approach validating your solution?*

    >> NOTE: The summary description is **NOT** a list of detailed comments on your code. If you start writing down an explanation of what each single line does, you are not moving in the right direction.

3. Your "personal tests" should cover all the Python methods that must be implemented. There's a penalty for each method that is **not** covered by your tests, so use `pycov` (and set up the GitHub actions) to check this aspect. Additionally, your tests must include at least one `assert` statement to be considered valid.

    >> Note: the more you test, the less likely the "grading (private) tests" will fail. And you cannot use public tests as private tests, nor consider public tests in your coverage report!
    
## Repo Structure

This (public) repository has the following structure:

```
.
├── README.md
├── requirements.txt
├── tests
│   ├── __init__.py
│   └── test_public_tests.py
└── traits
    ├── __init__.py
    └── interface.py

```

- `README.md`: this file
- `requirements.txt`: the file containing all and only the libraries you need to complete the task
- `tests`: contains the public tests
- `traits`: contain the abstract class to implement


> **NOTE** The content of this repository may change as a result of in-class discussion or the definition of new public test cases. For instance, new files inside the `tests` folder might be added, or their content might change anytime.
**It is your responsibility to ensure you always check out the latest version of this repository from GitHub.**

## Task Description

You must develop the backend system of a ticket reservation system called TRAITS, which stands for TRAIn Ticketing Service.
TRAITS allows its users to see train schedules, train connections, train status, buy train tickets, and reserve sits. Additionally, new users can be registered, new trains added to their schedule, existing schedules can be updated, and more (see below).

The backend system is the combination of two sub-systems that must interoperate via some Python code:

- A relational database (RDBMS) for transactional operations  to be implemented using `mariadb`

- A graph database (NoSQL) for other operations implemented using `neo4j`

It is your job to decide what information to store in which database, how to keep them synchronized, and how to orchestrate their operations.

For portability reasons, those components and the Python logic that coordinates them must be run in docker containers. Make sure you deploy each component into a separate docker container.

### Prerequisites
The following list defines the prerequisites for completing the assignment

- Docker
- Python 3.10
- MariaDB 10.6
- Neo4j 5.9.0

Additional Python libraries (to be installed with `pip`) are listed in the `requirements.txt` file.


## Main Features

TRAITS must implement three features used by guest users, registered users, and admin users. 

### Basic Features

All users can access the following basic features:

#### Search Train Connections (between two stations)
Return the connections from starting and ending stations, possibly including changes at interchanging stations. 

The search must be parametrized `travel time`, a `sorting criteria`, and the result can be `limited to a predefined number of connections`.

Travel time is a day of the year (use `day`, `month`, and `year`) and a time (use `hour` and `minute`) in 24h format.
Travel time can be either a departure or arrival time. Specifying a departure time ensures that the trip cannot start before the given time, whereas specifying an arrival time ensures that the trip cannot end after the given time.
By default, i.e., when not explicitly specified, travel time is `departure` and `now`.

Sorting criteria can be one (and only one) of the following:`overall travel time (ott)`, number of train changes (nc)`, `waiting time (wt)`, and `estimated price (ep)`. 

The overall travel time is the time from the beginning of the trip to its very end.

The number of train changes is the count of how many times the user must change the train during the trip.

The waiting time is the time the user spends waiting for a train, including the time spent waiting for the first train.

The estimated price is the overall (fixed) cost of the travel, which depends on the travel distance/time (`travel_price = travel time / 2`), and the (variable) cost for seat reservation, which depends on how many seats should be reserved (`reservation_price=number of trains * 2`).

For example, if the user travels with Train 1 from A to B to C and then boards Train 2 to reach D, the estimated price for the ticket plus reservations is:
- ```travel_price = [ tt(A,B) + tt(B,C) + tt(C,D) ] / 2```, where tt is the travel time from two stations (without counting the waiting time at each station or any delay)
- ```reservation_price = 2 * 2```

> Note: the actual price might be different if some seats cannot be reserved due to high demand

Sorting can be `ascending` or `descending`.
By default, i.e., when not explicitly specified, the sorting criteria is `overall travel time ascending` (so, the system must report the fastest connections first).

If starting or ending stations do not exist, or no connection between them is possible, the system must return an empty result.

In case the starting or ending stations are the same, the system must return a `ValueError.`

#### Check the status of a train
The user should be able to check the status of a train/connection: is the train operational? Is delayed? Etc.

### Advanced Features

Registered and only registered users can access the following advanced features:

#### Book Tickets and Reserve Seats
Given a train connection instance (e.g., on a given date/time), registered users can book tickets and optionally reserve seats. When the user decides to reserve seats, the system will try to reserve all the available seats automatically.

We make the following assumptions: 

- there is always a place on the trains so that tickets can always be bought
- the train seats are not numbered, so the system must handle only the number of passengers booked on a train and not each single seat
- The system grants only those seats that are effectively available at the moment of request; thus, overbooking on reserved seats is **not** possible
- Seats reservation **cannot** be done after booking a ticket
- A user can only reserve one seat on each train at the given time
- You do not have to implement a method to cancel reservations or provide a refund
 
#### Access Purchase History

Registered users can list the history of their past purchases, including the starting and ending stations, the day/time, total price, and **for each connection**, the price, and whether they reserved a seat.

The purchase history is always represented in descending starting time (at the top, the most recent trips).

### Admin Features:

Admin and only admin users can access the following special features:

#### TRAITS User Management
Admin can add/delete users. 

Users are identified by their (unique) email address and might have other attributes.

- Invalid addresses are not allowed (must raise a `ValueError`)
    >> NOTE: Check the validity of the email in the Database, not in Python!

- Duplicated addresses are not allowed (must raise a `ValueError`)

To follow GDPR, all the data about deleted users must also be deleted, including all the seat reservations (seats might become free). If the user does not exist, no exception is raised!

#### Train station management
Admin users can add and connect train stations and specify how long trains will travel between them.

Train stations cannot be duplicated (raise ValueError).
Any train station can be connected with any other train station except itself (so travel time cannot be zero!).
The same two train stations cannot be directly connected more than once.

As long as train stations are connected, trains can travel between them in any direction.  

Travel times must be at least one minute and cannot be more than one hour (raise ValueError otherwise).

We assume that 
- between connected stations, there are as many tracks as needed, so trains can travel freely (no need to check if at a given time the tracks are occupied by another train)
- any station has as many platforms as necessary (size does not matter)

#### Add/update/remove trains
Admin can add, update, or delete trains.

Updating a train can change their size (how many seats are available) and their status. The modification of the train has an immediate effect, but we assume that a train capacity cannot be reduced.

Admin can only toggle train status, i.e., trains can only be operational or nonoperational. When a train changes its status, its schedule(s) are affected.

Deleting a train should ensure consistency!
(Future) reservations are canceled, schedules/trips are canceled, etc. However, deleting a train must not change the purchase history of users.

#### Train Scheduling
Admin users can also add train schedules. A train schedule associates a train with a list of stations (stops) and their estimated waiting time (the train must stop at that station for the given time).

We assume that a train is never delayed, but it can be non-operational for some time (max three hours in a day). If a train is non-operational, its current and future schedules (on the same day) must be updated by adding a delay.

The delay is computed as the difference between when the train became non-operational and "now". The delay is rounded to the (next) minute.

We assume that:

- simple and nested transactions for reading, creating, updating and deleting elements from the database;
- queries that makes use of grouping and sorting; 
- transactions with the right isolation level(s)
- consistency checks and foreign keys management (cascade, etc.)
- views;
- users definition and grant permissions;
- database triggers;

### Recommendation System

The recommendation system must suggest products that clients are likely to buy after they bought other products.

The recommendation system is a special user of the RDBMS database. It can read some content from the RDBMS but cannot modify it.

The recommendation system offers the following APIs:

`bulk_update(self, month: int, year: int)`
`recommend(self, products: List, day: int, month: int, year: int, limit: int):`

The call `bulk_update` "imports" data from the RDBMS to build/update the graph. Data may contain duplicate entries; thus, those might be handled properly.

The call `recommend` generates the recommendations. In a nutshell, given a set of products p1, p2, ..., pn bought by a client c1 on date d1, the system uses the graph database to identify all the products P1, P2, ..., Pk (different than p1, p2, ..., pn) that other clients (c2, ..., cn) have bought together with p1 or p2 or ... pn in the *7* days before the purchase date d1.

Those products should be sorted by decreasing popularity, i.e., the amount of times they have been bought within *7* days from the purchase date d1. 

Finally, since the amount of products recommended by the system may be very large, the system should return only a limited number of products (`limit = k`).

For example, given the following list of purchases done by three clients over 6 days

| Client | Date | Cart       |
|--------|------|------------|
|     c1 |   1  | p1, p2     |
|     c2 |   1  | p1, p3     |
|     c2 |   2  | p1, p4     |
|     c3 |   4  | p2, p3, p4 |
|     c1 |   6  | p1, p2     |

The recommendation of a single product for a client that buys p2 and p4 on date 7, i.e.,  `recommend(products=[p2,p4],date=7,limit=1)`, is `[p1]`.

> Note: the syntax is only illustrative!

#### Explanation:

The recommendation date is 7, so we need to look at the 7 days before it (days 1 to 6).

> NOTE: the recommendation date is excluded!

During the period between date 1 and date 6:

- Along with p2:

    - c1 has bought p1 (on date 1)
    - c3 has bought p3, p4 (on date 4)
    - c1 has bought p1 (on date 6)

- Along with p4:

    - c2 has bought p1 (on date 2)
    - c3 has bought p3 (on date 4)

Thus, p1 and p3 have been bought with p2 or p4.

We need to sort p1 and p3 by their popularity:

- p1 has been bought 3 times
    - c1 on date 1
    - c2 on date 2
    - c1 on date 6   
- p3 has been bought 1 time
    - c3 on date 4

Thus, p1 is more popular than p3.

Finally, we return the first (i.e., `limit=1`) of the sorted products, which is p1.




