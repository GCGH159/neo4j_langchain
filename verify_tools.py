import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from app.tools.note_tools import execute_raw_cypher, get_graph_schema

def test_tools():
    print("--- Testing get_graph_schema ---")
    schema = get_graph_schema.invoke({})
    print(schema)
    
    print("\n--- Testing execute_raw_cypher (Query) ---")
    result = execute_raw_cypher.invoke({"query": "MATCH (n) RETURN count(n) as count"})
    print(result)
    
    print("\n--- Testing execute_raw_cypher (Write) ---")
    write_result = execute_raw_cypher.invoke({
        "query": "CREATE (t:TestNode {name: $name, timestamp: datetime()}) RETURN t.name as name",
        "params": {"name": "FlexTest"}
    })
    print(write_result)
    
    print("\n--- Testing execute_raw_cypher (Clean up) ---")
    cleanup_result = execute_raw_cypher.invoke({"query": "MATCH (t:TestNode {name: 'FlexTest'}) DELETE t"})
    print(cleanup_result)

if __name__ == "__main__":
    test_tools()
