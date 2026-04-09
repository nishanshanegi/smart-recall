# standard Postgres doesn't know what a "Vector" (mathematical representation of meaning) is. We have to enable it.
#Telling PostgreSQL to enable the vector extension

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base 
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# WHY: This creates the "Base" class that all your other models (like VaultItem) inherit from.
Base = declarative_base() 

def init_db():
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.commit()
    # WHY: This uses the 'Base' we defined above to create all tables
    Base.metadata.create_all(bind=engine)


# with engine.connect() as conn:
# WHAT is conn? It stands for Connection.
# HOW it works: The with statement is a "Context Manager." It opens the door to the database, gives you the conn object to talk through, and automatically closes the door when the block of code is finished.
# WHY use conn here instead of a Session? Sessions are for high-level data (Adding a user). conn is for low-level "Administrative" tasks (like installing the vector extension).
# Base.metadata.create_all(bind=engine)
# WHAT: This is the "Magic Button."
# HOW: It looks at every script in your project that inherited from Base, finds the table definitions, and says: "Okay Postgres, create these tables if they don't exist yet."