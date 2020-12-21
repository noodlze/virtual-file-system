### About
A simple web-based file(files/folders) system, with python as the backend, data persisted on a postgres db and html+jquery as frontend.

A simple command-like web interface supports the following commands:
1.`cd [FOLDER]`
2.`ls [-l] [LEVEL]`: -l provides more details about folder contents
3.`cr [-p] PATH [DATA]` cr is equivalent to mkdir, -p indicates to create the dest path if required, DATA is only specified if the dest is a file
4.`mv SOURCE/SOURCES DESTINATION` move one or many source items to a destination
5.`rm PATH` delete file/folder

### How to run
1. ENVIRONMENT VARIABLES
To run locally, first create a  postgres database, which is used to store the file system.
Then export env variable ENGINE_URI to the path of the postgres db:
i.e.
`ENGINE_URI='postgresql+psycopg2://thuypham:root@localhost:5432/file_system'`
Flask config also requires SECRET_KEY for session to work
i.e.`SECRET_KEY='vnVl8ycSmt6b6veHk4KP'`

2. DB upgrade using alembic migrations(inside Procfile)

3. Run using command(you can have additional flask options as params): `$PWD/venv/bin/python manage.py runserver -d --threaded`

### Thoughts
A really interesting problem on how to store hierarchical data in a relational db.

Reliability(how to server deals with incorrect/untested command cases,errors and exceptions such that data integrity is maintained?) and scalability(performance of ls with highly nested subdirectories) were prioritised.

Maintainability of solution needs improving. Instead of having one api and a controller that delegates execution of user command to the relevant backend server, there should be an api and corresponding controller for each command(should look into implementing Facebook's flux architecture).

The ui has a lot of room for improvement.Need to move to Vue.js so it is easier to implement more complex and interactive UI. Logic on how to display `ls` command results should be moved from backend to frontend.
