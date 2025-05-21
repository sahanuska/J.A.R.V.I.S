from functools import wraps
from flask import Flask, redirect, render_template, request, session, jsonify
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
# No imports should be named 'uuid.py' to avoid conflicts
# Use absolute imports to avoid issues with naming conflicts
import os
import redis

from uuid import uuid4  # Import specific function instead of whole module
from functools import wraps
from flask import Flask, redirect, render_template, request, session, jsonify
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras

# Load environment variables from .env file
load_dotenv()


os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "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"
os.environ["GOOGLE_API_KEY"] = "AIzaSyDpD2Ltm4fQFDrLvf1nAMBazrKoKHGG5qI"
app = Flask(__name__)
app.config["SESSION_TYPE"] = "redis"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")

app.config["SESSION_REDIS"] = redis.from_url("redis://default:DgGuIhzlOOl4XMQORQJSAssnURDiD4M7@redis-14137.c44.us-east-1-2.ec2.redns.redis-cloud.com:14137")
Session(app)

# Neon DB configuration
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://neondb_owner:npg_TSB9rnecdJC1@ep-gentle-block-a47j9qn2-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require")

# Extract endpoint ID from the DATABASE_URL
def get_endpoint_id():
    # Parse the endpoint ID from the hostname part of the URL
    # Example: postgresql://user:pass@ep-cool-name-123456.us-east-2.aws.neon.tech/dbname
    # Endpoint ID would be: ep-cool-name-123456
    try:
        import re
        match = re.search(r'@([^.]+)', DATABASE_URL)
        if match:
            return match.group(1)
        return None
    except:
        return None

# Database connection function
def get_db_connection():
    endpoint_id = get_endpoint_id()
    
    # If we can extract an endpoint ID, append it to the connection options
    if endpoint_id:
        # Check if there are already parameters in the URL
        if '?' in DATABASE_URL:
            connection_string = f"{DATABASE_URL}&options=endpoint%3D{endpoint_id}"
        else:
            connection_string = f"{DATABASE_URL}?options=endpoint%3D{endpoint_id}"
    else:
        connection_string = DATABASE_URL
    
    conn = psycopg2.connect(connection_string, sslmode='require')
    conn.autocommit = True
    return conn

# Create tables if they don't exist
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Create users table if it doesn't exist
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            mail TEXT NOT NULL,
            hash TEXT NOT NULL
        )
    """)
    
    conn.commit()
    cur.close()
    conn.close()

# Initialize database on startup
init_db()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return render_template("login.html")
        return f(*args, **kwargs)
    return decorated_function

def init_app():
    model = ChatGoogleGenerativeAI(model="gemini-1.5-flash")

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "act as a robot and your name is Jarvis you know your job extremely well"),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    workflow = StateGraph(state_schema=MessagesState)

    def call_model(state: MessagesState):
        chain = prompt | model
        response = chain.invoke(state)
        return {"messages": response}

    workflow.add_edge(START, "model")
    workflow.add_node("model", call_model)

    # Persistent memory across reruns
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)

    config = {"configurable": {"thread_id": "abc123"}}
    return app, memory, config

# Initialize app, memory, and config
app_data, memory, config = init_app()

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = "0"
    response.headers["Pragma"] = "no-cache"
    return response

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    session.clear()
    if request.method == 'POST':
        if not request.form.get('username'):
            return render_template('error.html', error='Must Provide Username')
        elif not request.form.get('password'):
            return render_template('error.html', error='Must Provide Password')
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        cur.execute(
            'SELECT * FROM users WHERE username = %s', (request.form.get('username'),))
        rows = cur.fetchall()
        
        cur.close()
        conn.close()
        
        if len(rows) != 1 or not check_password_hash(
            rows[0]['hash'], request.form.get('password')
        ):
            return render_template('error.html', error='Invalid Username or password')
        
        session['user_id'] = rows[0]['id']
        session['config_id'] = str(uuid4())  # Use uuid4() instead of uuid.uuid4()

        return redirect('/')
    else:
        return render_template('login.html')

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("confirmation")
        email = request.form.get("email")  # Get email from form
        
        if not username or not password or not confirm or not email:
            return render_template("error.html", error="Enter all Fields")
        if password != confirm:
            return render_template("error.html", error="Passwords do not Match")
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Check if username exists
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        exist = cur.fetchall()
        
        if len(exist) != 0:
            cur.close()
            conn.close()
            return render_template("error.html", error="Username already exists")
            
        hashed = generate_password_hash(password)
        
        # Insert new user
        cur.execute(
            "INSERT INTO users (username, mail, hash) VALUES (%s, %s, %s) RETURNING id", 
            (username, email, hashed)
        )
        user_id = cur.fetchone()[0]
        
        conn.commit()
        cur.close()
        conn.close()
        
        session["user_id"] = user_id
        return redirect("/login")
    else:
        return render_template("register.html")

@app.route('/chat', methods=['POST'])
@login_required
def chat():
    user_input = request.json.get("message")
    user_message = HumanMessage(content=user_input)
    config_id = session.get("config_id", "default_config")
    config = {"configurable": {"thread_id": config_id}}

    # Invoke the model and get a response
    output = app_data.invoke({"messages": [user_message]}, config)
    bot_response = output["messages"][-1].content

    return jsonify({"response": bot_response})

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    session.clear()
    return render_template('login.html')


if __name__ == '__main__':
    app.run(debug=True)
