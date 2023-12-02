from flask import Flask, render_template
import mysql.connector

app = Flask(__name__)

# MySQL database configuration
db = mysql.connector.connect(
    host="localhost",
    user="Jeff",
    password="Orca1212$$",
    database="ash"
)

cursor = db.cursor()

@app.route('/order_history')
def order_history():
    # Retrieve order history from the database
    cursor.execute("SELECT * FROM orders")
    orders = cursor.fetchall()

    return render_template('order_history.html', orders=orders)

if __name__ == '__main__':
    app.run(debug=True)
