# SIMPLE REMOTE MCP SERVER
# STEPS TO CREATE A SIMPLE REMOTE MCP SERVER
# 1. Install uv
# 2. Create new folder
# 3. Open the folder in vs code
# 4. Uv init.
# 5. Uv add fastmcp
# 6. Create a simple server
# 7. Run the server uv run main.py
# 8. Test the server using mcp inspector
# 9. Create a GitHub repo
# 10. Git init
# 11. git add.
# 12. git commit -m "Initial commit: Simple MCP server"
# 13. git remote add origin
# https://github.com/yourusername/simple-mcp-server.git
# 14. git push-u origin main
# 15. Create an account on FastMCP cloud
# 16. Deploy on FastMCP cloud

# CODE:
# from fastmcp import FastMCP
# import random
# import json

# # Create the FastMCP server instance
# mcp = FastMCP("Simple Calculator Server")

# # Tool: Add two numbers
# @mcp.tool
# def add(a: int, b: int) -> int:
#     """Add two numbers together.

#     Args:
#         a: First number
#         b: Second number

#     Returns:
#         The sum of a and b
#     """
#     return a + b

# # Tool: Generate a random number
# @mcp.tool
# def random_number(min_val: int = 1, max_val: int = 100) -> int:
#     """Generate a random number within a range.

#     Args:
#         min_val: Minimum value (default: 1)
#         max_val: Maximum value (default: 100)

#     Returns:
#         A random integer between min_val and max_val
#     """
#     return random.randint(min_val, max_val)

# # Resource: Server information
# @mcp.resource("info://server")
# def server_info() -> str:
#     """Get information about this server."""
#     info = {
#         "name": "Simple Calculator Server",
#         "version": "1.0.0",
#         "description": "A basic MCP server with math tools",
#         "tools": ["add", "random_number"],
#         "author": "Your Name"
#     }
#     return json.dumps(info, indent=2)

# if __name__=="__main__":
#     mcp.run(transport="http",host="0.0.0.0",port=8000) #default is STDIO

# CODE BLOCK V2
# # ExpenseTracker REMOTE MCPSERVER
# from fastmcp import FastMCP
# import os
# import sqlite3

# DB_PATH=os.path.join(os.path.dirname(__file__),"expenses.db")
# CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")
# mcp=FastMCP(name="ExpenseTracker")

# def init_db():
#     with sqlite3.connect(DB_PATH) as c:
#         c.execute("""
#             CREATE TABLE IF NOT EXISTS expenses(
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 date TEXT NOT NULL,
#                 amount REAL NOT NULL,
#                 category TEXT NOT NULL,
#                 subcategory TEXT DEFAULT '',
#                 note TEXT DEFAULT ''
#             )
#         """)
# init_db()

# @mcp.tool
# def add_expense(date, amount, category, subcategory="", note=""):
#     '''Add a new expense entry to the database.'''
#     with sqlite3.connect(DB_PATH) as c:
#         cur = c.execute(
#             "INSERT INTO expenses(date, amount, category, subcategory, note) VALUES (?,?,?,?,?)",
#             (date, amount, category, subcategory, note)
#         )
#         return {"status": "ok", "id": cur.lastrowid}



# @mcp.tool()
# def list_expenses(start_date, end_date):
#     '''List expense entries within an inclusive date range.'''
#     with sqlite3.connect(DB_PATH) as c:
#         cur = c.execute(
#             """
#             SELECT id, date, amount, category, subcategory, note
#             FROM expenses
#             WHERE date BETWEEN ? AND ?
#             ORDER BY id ASC
#             """,
#             (start_date, end_date)
#         )
#         cols = [d[0] for d in cur.description]
#         return [dict(zip(cols, r)) for r in cur.fetchall()]

# @mcp.tool()
# def summarize(start_date, end_date, category=None):
#     '''Summarize expenses by category within an inclusive date range.'''
#     with sqlite3.connect(DB_PATH) as c:
#         query = (
#             """
#             SELECT category, SUM(amount) AS total_amount
#             FROM expenses
#             WHERE date BETWEEN ? AND ?
#             """
#         )
#         params = [start_date, end_date]

#         if category:
#             query += " AND category = ?"
#             params.append(category)

#         query += " GROUP BY category ORDER BY category ASC"

#         cur = c.execute(query, params)
#         cols = [d[0] for d in cur.description]
#         return [dict(zip(cols, r)) for r in cur.fetchall()]
    
# @mcp.resource("expense://categories",mime_type="application/json")
# def categories():
#     with open(CATEGORIES_PATH,"r",encoding="utf-8") as f:
#         return f.read()

# if __name__=="__main__":
#     mcp.run(transport="http",host="0.0.0.0",port=8000) 

# # if db file i not available use this command to run file and create db file: uv run src/demo_remote_mcp_server/main.py 


# CODE BLOCK V3
# This code is used to solve the error saying the database of mcp server is read-only, so it won’t accept new entries(writes). Along with that it also solves another i.e. our mcp server earlier ran synchronously which means if one user is using a specific tool then that tools becomes unavailable to other users and they have to wait until first finishes, async solves that
from fastmcp import FastMCP
import os
import aiosqlite  # Changed: sqlite3 → aiosqlite
import tempfile
# Use temporary directory which should be writable
TEMP_DIR = tempfile.gettempdir()
DB_PATH = os.path.join(TEMP_DIR, "expenses.db")
CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")

print(f"Database path: {DB_PATH}")

mcp = FastMCP("ExpenseTracker")

def init_db():  # Keep as sync for initialization
    try:
        # Use synchronous sqlite3 just for initialization
        import sqlite3
        with sqlite3.connect(DB_PATH) as c:
            c.execute("PRAGMA journal_mode=WAL")
            c.execute("""
                CREATE TABLE IF NOT EXISTS expenses(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    subcategory TEXT DEFAULT '',
                    note TEXT DEFAULT ''
                )
            """)
            # Test write access
            c.execute("INSERT OR IGNORE INTO expenses(date, amount, category) VALUES ('2000-01-01', 0, 'test')")
            c.execute("DELETE FROM expenses WHERE category = 'test'")
            print("Database initialized successfully with write access")
    except Exception as e:
        print(f"Database initialization error: {e}")
        raise

# Initialize database synchronously at module load
init_db()

@mcp.tool()
async def add_expense(date, amount, category, subcategory="", note=""):  # Changed: added async
    '''Add a new expense entry to the database.'''
    try:
        async with aiosqlite.connect(DB_PATH) as c:  # Changed: added async
            cur = await c.execute(  # Changed: added await
                "INSERT INTO expenses(date, amount, category, subcategory, note) VALUES (?,?,?,?,?)",
                (date, amount, category, subcategory, note)
            )
            expense_id = cur.lastrowid
            await c.commit()  # Changed: added await
            return {"status": "success", "id": expense_id, "message": "Expense added successfully"}
    except Exception as e:  # Changed: simplified exception handling
        if "readonly" in str(e).lower():
            return {"status": "error", "message": "Database is in read-only mode. Check file permissions."}
        return {"status": "error", "message": f"Database error: {str(e)}"}
    
@mcp.tool()
async def list_expenses(start_date, end_date):  # Changed: added async
    '''List expense entries within an inclusive date range.'''
    try:
        async with aiosqlite.connect(DB_PATH) as c:  # Changed: added async
            cur = await c.execute(  # Changed: added await
                """
                SELECT id, date, amount, category, subcategory, note
                FROM expenses
                WHERE date BETWEEN ? AND ?
                ORDER BY date DESC, id DESC
                """,
                (start_date, end_date)
            )
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in await cur.fetchall()]  # Changed: added await
    except Exception as e:
        return {"status": "error", "message": f"Error listing expenses: {str(e)}"}

@mcp.tool()
async def summarize(start_date, end_date, category=None):  # Changed: added async
    '''Summarize expenses by category within an inclusive date range.'''
    try:
        async with aiosqlite.connect(DB_PATH) as c:  # Changed: added async
            query = """
                SELECT category, SUM(amount) AS total_amount, COUNT(*) as count
                FROM expenses
                WHERE date BETWEEN ? AND ?
            """
            params = [start_date, end_date]

            if category:
                query += " AND category = ?"
                params.append(category)

            query += " GROUP BY category ORDER BY total_amount DESC"

            cur = await c.execute(query, params)  # Changed: added await
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in await cur.fetchall()]  # Changed: added await
    except Exception as e:
        return {"status": "error", "message": f"Error summarizing expenses: {str(e)}"}

@mcp.resource("expense:///categories", mime_type="application/json")  # Changed: expense:// → expense:///
def categories():
    try:
        # Provide default categories if file doesn't exist
        default_categories = {
            "categories": [
                "Food & Dining",
                "Transportation",
                "Shopping",
                "Entertainment",
                "Bills & Utilities",
                "Healthcare",
                "Travel",
                "Education",
                "Business",
                "Other"
            ]
        }
        
        try:
            with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            import json
            return json.dumps(default_categories, indent=2)
    except Exception as e:
        return f'{{"error": "Could not load categories: {str(e)}"}}'

# Start the server
if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)