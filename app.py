#need to work on user support i.e. a login in button. Once we get users we can just copy, paste, and edit for admins and warehouse

#import stripe
from flask import Flask, render_template, request, redirect, send_from_directory, session, url_for
#from flask_session import Session
import os
import mysql.connector
import datetime

#PEOPLE_FOLDER = os.path.join('imgs', 'oil')

app = Flask(__name__)
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
#app.config["SESSION_PERMANENT"] = False
#app.config["SESSION_TYPE"] = "filesystem"
#stripe.api_key = 'your_stripe_secret_key'

#app.config['UPLOAD_FOLDER'] = PEOPLE_FOLDER

# MySQL database configuration
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="default"
)

#cursor is used to access the database
cursor = db.cursor()

# Create orders table if not exists
cursor.execute("""
    CREATE TABLE IF NOT EXISTS LegacyProducts (
    part_number INT PRIMARY KEY,
    part_name   VARCHAR(32),
    description VARCHAR(255),
    weight DECIMAL(10, 2),
    picture_link VARCHAR(255),
    price DECIMAL(10, 2)
    )
""")
#if table does not exist we have to make it and commit it to the database
db.commit()

#Gets all the data from Legacy Products
def get_products():
    cursor.execute("SELECT * FROM LegacyProducts")  
    data = cursor.fetchall() #fetches all the tuples
    return data

#'/' refers to the initial webpage
@app.route('/')
def index():
    # Initialize the shopping cart in the session
    if 'cart' not in session:
        print("Initializing shopping cart in the session.")
        session['cart'] = [] #visual for what the user has selected
    products=get_products() #gets data
    #sends the server to the catalog html
    return render_template('catalog.html',products=products)

#the main page that has all the data
@app.route('/catalog')
def cat():
    #if cart does not exist in session the user cannot add things to it
    if 'cart' not in session:
        print("Initializing shopping cart in the session.")
        session['cart'] = []
    products=get_products()
    return render_template('catalog.html',products=products, cart=session['cart'])

#we want to add items to a cart
@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    cursor.execute("SELECT * FROM LegacyProducts")
    catalog = cursor.fetchall()
    product = next((item for item in catalog if item[0] == product_id), None)
    if product:
        quantity = int(request.form.get('quantity', 0))  # Default to 1 if quantity is not provided. Need to change this to add the second database
        cart_item = {'id': product[0], 'name': product[5], 'price': product[4], 'quantity': quantity} #create cart that holds information on each item
        session['cart'].append(cart_item) #add the object to the session cart
        #session['cart'].append(product)
        session.modified = True
    return redirect(url_for('cat')) #sends us to the cat function

#remove items from the cart
@app.route('/remove_from_cart/<int:product_id>')
def remove_from_cart(product_id):
    session['cart'] = [item for item in session['cart'] if item['id'] != product_id]
    session.modified = True
    return redirect(url_for('cat'))

#gets the total cost 
@app.route('/cart')
def view_cart():
    total_price = sum(float(item['price']) for item in session['cart']) #this needs to be looked at, doesnt multiply item by quantity
    return render_template('cart.html', cart=session['cart'], total_price=round(total_price,2)) #sends us to the cart which will be the checkout menu

#needs to be edited to allow users to input information.
@app.route('/checkout', methods=['POST'])
def checkout():
    # Perform checkout process with Stripe payment
    checkout_session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{'price_data': {'currency': 'usd', 'product_data': {'name': item['name']}, 'unit_amount': int(item['price'] * 100), 'quantity': 1}} for item in session['cart']],
        mode='payment',
        success_url=request.url_root + 'success',
        cancel_url=request.url_root + 'cancel',
    )
    return {'id': checkout_session.id}

#was a temp function for cart
@app.route('/land', methods=['POST'])
def land():
    print('yes')
    ProdNam = request.form['ProdNam']
    print(ProdNam)
    return render_template('/land.html')

#will be used to display orders
@app.route('/order_history')
def order_history():
    # Retrieve order history from the database
    cursor.execute("SELECT * FROM orders")
    orders = cursor.fetchall()
    for crack in orders:
        print(crack)
    return render_template('order_history.html', orders=orders)

#will be used to submit orders 
@app.route('/submit_order', methods=['POST'])
def submit_order():
    order_id = request.form['order_id']
    customer_id = request.form['customer_id']
    total_price = request.form['total_price']
    order_date = datetime.datetime.now()
    shipping_handling_charge = request.form['shipping_handling_charge']
    status = request.form['status']
    authorization_number = request.form['authorization_number']
    
    # Insert order into the database
    cursor.execute("INSERT INTO orders (order_id, customer_id, order_date, total_price, shipping_handling_charge, status, authorization_number) VALUES (%d, %d, %d, %d,%d,%s,%s)",
                   (order_id, customer_id, order_date, total_price, shipping_handling_charge, status, authorization_number))
    db.commit()

    return redirect('/order_history.html')

if __name__ == '__main__':
    app.run(debug=True)
