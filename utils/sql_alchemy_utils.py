import sqlalchemy as sa

engine = sa.create_engine("sqlite:///databases/users/users_macro_nutrition.db",
    connect_args={'timeout': 10}
                          )
connection = engine.connect()

metadata = sa.MetaData()

user_table = sa.Table(
    "users_nutrition_macro",
    metadata,
    sa.Column("id", sa.String, primary_key=True),
    sa.Column("weight", sa.Integer),
    sa.Column("height", sa.Integer),
    sa.Column("age", sa.Integer),
    sa.Column("activity", sa.Integer),
    sa.Column("goal", sa.Integer),
    sa.Column("gender", sa.String))

def initialize_database():
    metadata.create_all(engine)

def insert_user_data(id, weight, height, age, activity, goal, gender):
    print("Inserting user data ",id, weight, height, age, activity, goal, gender)
    print("Checking if user exists ",user_table.c.id == id)
    with engine.connect() as connection:
        with connection.begin():
            select_stmt = sa.select(user_table).where(user_table.c.id == id)
            result = connection.execute(select_stmt).fetchone()
            print("Result ",result)
            if result:
                print("User exists, performing an update")  
                update_stmt = (
                    sa.update(user_table)
                    .where(user_table.c.id == id)
                    .values(
                        weight=weight,
                        height=height,
                        age=age,
                        activity=activity,
                        goal=goal,
                        gender=gender
                    )
                )
                connection.execute(update_stmt)
            else:
                print("User does not exist, performing an insert")
                insert_stmt = sa.insert(user_table).values(
                    id=id,
                    weight=weight,
                    height=height,
                    age=age,
                    activity=activity,
                    goal=goal,
                    gender=gender
                )
                connection.execute(insert_stmt)

def get_user_data(id):
    with engine.connect() as connection:
        with connection.begin():
            query = user_table.select().where(user_table.c.id == id)
            result = connection.execute(query)
            return result.fetchone()