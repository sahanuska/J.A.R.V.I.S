
from cs50 import SQL
from functools import wraps
from flask import Flask, redirect, render_template, request, session,jsonify
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from werkzeug.security import check_password_hash, generate_password_hash
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
import os
import uuid


os.environ["LANGCHAIN_TRACING_V2"]="true"
os.environ["LANGCHAIN_API_KEY"]="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"
os.environ["GOOGLE_API_KEY"] = "AIzaSyDpD2Ltm4fQFDrLvf1nAMBazrKoKHGG5qI"
app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
db = SQL("sqlite:///user.db")

db.execute("""CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    hash TEXT NOT NULL
)""")

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
            ("system", "act as users friend anuska,and user is your crush"),
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
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        if not request.form.get("username"):
            return render_template("error.html", error="Must Provide Username")
        elif not request.form.get("password"):
            return render_template("error.html", error="Must Provide Password")
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username"))
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return render_template("error.html", error="Invalid Username or password")
        session["user_id"] = rows[0]["id"]
        session["config_id"] = str(uuid.uuid4())

        return redirect("/")
    else:
        return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("confirmation")
        if not username or not password or not confirm:
            return render_template("error.html", error="Enter all Feilds")
        if password != confirm:
            return render_template("error.html", error="Passwords donot Match")
        exist = db.execute("SELECT * FROM users WHERE username=?", username)
        if len(exist) != 0:
           return render_template("error.html", error="Username already exists")
        hashed = generate_password_hash(password)
        db.execute("INSERT into users (username,hash) VALUES (?,?)", username, hashed)
        user = db.execute("SELECT id FROM users WHERE username=?", username)
        session["user_id"] = user[0]["id"]
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
