from flask import Flask, render_template, request, redirect
import os
import mysql.connector
import datetime

PEOPLE_FOLDER = os.path.join('imgs', 'oil')

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = PEOPLE_FOLDER
# MySQL database configuration
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="default"
)

cursor = db.cursor()

@app.route('/')
def get_image():
    filename= os.path.join(app.config['UPLOAD_FOLDER'],'imgs/oil.jpeg')
    return render_template("order_form.html", user_image = filename)
def index():
    return render_template('order_history.html')


@app.route('/order_history')
def order_history():
    # Retrieve order history from the database
    cursor.execute("SELECT * FROM orders")
    orders = cursor.fetchall()
    for crack in orders:
        print(crack)
    return render_template('order_history.html', orders=orders)

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

    return redirect('/order_history')

if __name__ == '__main__':
    app.run(debug=True)
