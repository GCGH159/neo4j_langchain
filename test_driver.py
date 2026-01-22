from neo4j import GraphDatabase
from config import config

uri = config.NEO4J_URI
user = config.NEO4J_USERNAME
password = config.NEO4J_PASSWORD

print(f"Connecting to {uri} as {user}...")

try:
    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        print("Testing basic return...")
        result = session.run("RETURN 1 as val")
        val = result.single()["val"]
        print(f"Success! val={val}")
        
        print("\nTesting db.schema.visualization()...")
        try:
            session.run("CALL db.schema.visualization()").consume()
            print("Success: db.schema.visualization() works")
        except Exception as e:
            print(f"Failed: {e}")

        print("\nTesting apoc.meta.data()...")
        try:
            session.run("CALL apoc.meta.data()").consume()
            print("Success: apoc.meta.data() works")
        except Exception as e:
            print(f"Failed: {e}")
            
    driver.close()
except Exception as e:
    print(f"Driver connection failed: {e}")
