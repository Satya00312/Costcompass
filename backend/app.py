from flask import Flask, request, jsonify,session

from flask_cors import CORS
import logging

from scraping.scraper import scrape_product_prices_by_specs, scrape_product_prices_by_make_model
import mysql.connector
import bcrypt
import secrets



app = Flask(__name__)
CORS(app)

app.secret_key = secrets.token_hex(16)


def make_session_permanent():
    session.permanent = True

# Database configuration
db_config = {
    'user': 'root',  
    'password': '1234',  
    'host': 'localhost',
    'database': 'costcompass',
}

@app.route('/')
def welcome():
    logging.info("Welcome endpoint called.")
    return "Welcome to the Cost Compass API"

@app.route('/register', methods=['POST'])
def register():
    # Get and log incoming data
    data = request.get_json()
    print(f"Received registration data: {data}")

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required!'}), 400

    # Database connection and cursor
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    try:
        # Check for existing username
        print("Checking if username already exists...")
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            print("Username already exists.")
            return jsonify({'message': 'User already exists!'}), 400

        # Hash password
        print("Hashing password...")
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        print("Password hashed, inserting into database.")

        # Insert into database
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
        conn.commit()

        print("User registered successfully.")
        return jsonify({'message': 'User registered successfully!'}), 201

    except mysql.connector.Error as err:
        print(f"Database error during registration: {err}")
        return jsonify({'message': f'Database error: {str(err)}'}), 500

    finally:
        cursor.close()
        conn.close()

# Login route
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if(username!="venu" and password!="1234"):
        return jsonify({'message': 'Invalid username or password!'}), 401

    return jsonify({'message': 'Login successful!'}),200
# Login route
'''@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    try:
        # Query to fetch the hashed password from the database
        cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
        result = cursor.fetchone()

        if not result or not bcrypt.checkpw(password.encode('utf-8'), result[0].encode('utf-8')):
            return jsonify({'message': 'Invalid username or password!'}), 401

        # After successful login, store the username in the session
        session['username'] = username
        return jsonify({'message': 'Login successful!'}), 200

    except mysql.connector.Error as err:
        return jsonify({'message': f'Database error: {str(err)}'}), 500

    finally:
        cursor.close()
        conn.close()'''

# Make and model query route
@app.route('/make-model-query', methods=['POST'])
def make_model_query():
    data = request.json
    try:
        username = session.get('username')
        
        
        product_name = data.get('product_name')
        make = data.get('make')
        model = data.get('model')

        # Ensure make and model are treated as strings
        make_str = '+'.join(make) if isinstance(make, list) else make
        model_str = '+'.join(model) if isinstance(model, list) else model

        logging.info(f"Received query: {product_name} {make_str} {model_str}")

        results = scrape_product_prices_by_make_model(product_name, make_str, model_str)


        

        if 'error' in results:
            logging.error(f"Scraping error: {results['error']}")
            return jsonify({'message': results['error']}), 500
        
        if not results:
            return jsonify({'message': 'No products found'}), 404
        


        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        # Insert the query details
        query = """
            INSERT INTO history (username, product, make)
            VALUES (%s, %s, %s)
        """
        
        cursor.execute(query, (username, product_name, make))
        conn.commit()
        
        # Close the connection
        cursor.close()
        conn.close()

        return jsonify(results), 200
    except Exception as e:
        logging.error(f"Error processing query: {e}")
        return jsonify({'message': 'An error occurred while processing the query.'}), 500

# Specification query route
@app.route('/specification-query', methods=['POST'])
def specification_query():
    try:
        data = request.get_json()
        product_name = data.get('product_name')
        specifications = data.get('specifications')

        # Ensure specifications is a string
        if isinstance(specifications, list):
            specifications = ', '.join(specifications)  # or join with a different separator

        products = scrape_product_prices_by_specs(product_name, specifications)
        return jsonify(products), 200
    except Exception as e:
        logging.error(f"Error occurred: {e}")
        return jsonify({"message": "An error occurred while processing the query."}), 500
@app.route('/api/scrape', methods=['POST'])
def scrape_product():
    data = request.json
    product_name = data.get("product")
    
    # Perform the scraping for `product_name`
    scraped_data = perform_scraping(product_name)  # Define this function based on your scraper
    return jsonify(scraped_data)

if __name__ == '__main__':
    app.run(debug=True)
