import click
from api.models import db, User, Planet, Character

"""
In this file, you can add as many commands as you want using the @app.cli.command decorator
Flask commands are usefull to run cronjobs or tasks outside of the API but sill in integration 
with youy database, for example: Import the price of bitcoin every night as 12am
"""
def setup_commands(app):
    
    """ 
    This is an example command "insert-test-users" that you can run from the command line
    by typing: $ flask insert-test-users 5
    Note: 5 is the number of users to add
    """
    @app.cli.command("insert-test-users") # name of our command
    @click.argument("count") # argument of out command
    def insert_test_users(count):
        print("Creating test users")
        for x in range(1, int(count) + 1):
            user = User()
            user.username = "test_user" + str(x) 
            user.password = "123456"
            db.session.add(user)
            try:
                db.session.commit()
                print("User: ", user.username, " created.")
            except Exception as e:
                db.session.rollback()
                print(f"Error creating user: {e}")

        print("All test users created")

    @app.cli.command("insert-test-data")
    def insert_test_data():
        planets = [
            {"name": "Tatooine", "climate": "arid", "terrain": "desert", "population": 200000},
            {"name": "Alderaan", "climate": "temperate", "terrain": "grasslands, mountains", "population": 2000000000},
            {"name": "Yavin IV", "climate": "tropical", "terrain": "jungle, rainforests", "population": 1000},
            # Add more planets...
        ]
        characters = [
            {"name": "Luke Skywalker", "height": 172, "hair_color": "blond", "eye_color": "blue", "gender": "male"},
            {"name": "Darth Vader", "height": 202, "hair_color": "none", "eye_color": "yellow", "gender": "male"},
            {"name": "Leia Organa", "height": 150, "hair_color": "brown", "eye_color": "brown", "gender": "female"},
            # Add more characters...
        ]

        for planet_data in planets:
            planet = Planet(**planet_data)
            db.session.add(planet)

        for character_data in characters:
            character = Character(**character_data)
            db.session.add(character)

        try:
            db.session.commit()
            print("Test data inserted successfully.")
        except Exception as e:
            db.session.rollback()
            print(f"Error inserting test data: {e}")
