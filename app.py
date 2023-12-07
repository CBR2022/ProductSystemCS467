import random
from flask import Flask, render_template, request, redirect, send_from_directory, session, url_for
import os
import mysql.connector
from datetime import datetime, date
from ccAuth import authorize_cc

PEOPLE_FOLDER = os.path.join('imgs', 'oil')

app = Flask(__name__)
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
#app.config["SESSION_PERMANENT"] = False
#app.config["SESSION_TYPE"] = "filesystem"

app.config['UPLOAD_FOLDER'] = PEOPLE_FOLDER

# MySQL database configuration
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="proj467"
)
# legacydb connection
legaceydb = mysql.connector.connect(
    host = "blitz.cs.niu.edu",
    port = 3306,
    user = "student",
    password = "student",
    database = "csci467"
)
#cursors for database
cursor = db.cursor()
legacycursor = legaceydb.cursor()
#displays products and their quantity on the page
def get_products():
    cursor.execute("select * from inventory")
    data = cursor.fetchall()

    legacycursor.execute("select * from parts")
    legacydata = legacycursor.fetchall()

    # Perform a simple join operation to merge the data
    joined_data = [(row1[0], row1[1],row1[2], row1[3],row1[4], row2[1]) for row1 in legacydata for row2 in data if row1[0] == row2[0]]
    for row in joined_data:
        print(row)
    return joined_data
#launches the first page
@app.route('/')
def index():
    return render_template('index.html')
#creates a cart and launches the catalog
@app.route('/catalog')
def cat():
    if 'cart' not in session:
        print("Initializing shopping cart in the session.")
        session['cart'] = []
    products=get_products()
    return render_template('catalog.html',products=products, cart=session['cart'])
#launches admin and gets information from shipping and handling
@app.route('/admin')
def admin():
    chCur = db.cursor()
    chCur.execute("select * from ShippingHandlingCharges")
    data = chCur.fetchall()
    return render_template('Admin.html',Charges=data)

#allows for changes to be made to shipping and handling once the button is clicked
@app.route('/admin_update/<int:chargeid>',methods=['GET', 'POST'] )
def admin_update(chargeid):
    cFee = float(request.form.get('cFee', 0)) #is the fee for shipping and handling that the admin wants to change
    chCur = db.cursor()
    chCur.execute("select charge from ShippingHandlingCharges where weight_bracket = %s", (chargeid,))
    idata = chCur.fetchone()
    chCur.execute("update ShippingHandlingCharges set charge = %s where weight_bracket = %s", (cFee, chargeid))
    db.commit()
    chCur.close()
    return redirect(url_for('admin'))

@app.route('/rdesk')
def rdesk():
    products=get_products()
    return render_template('rdesk.html',products=products)

#updates the quantity in inventory for a specific part
@app.route('/rdesk_update/<int:product_id>',methods=['GET', 'POST'] )
def rdesk_update(product_id):
    quantity = int(request.form.get('quantity', 0)) #how much the person wants to change quantity
    chCur = db.cursor()
    chCur.execute("select quantity_on_hand from inventory where part_number = %s", (product_id,)) #get info regarding a certain part
    idata = chCur.fetchone()
    for ilist in idata:
        chCur.execute("update inventory set quantity_on_hand = %s where part_number = %s", (quantity, product_id))#execute the update
        db.commit()
    chCur.close()
    return redirect(url_for('rdesk'))

#adds a product item to the cart
@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    catalog = get_products()#we need to pull the catalog
    invt = int(request.form.get('invt', 0))#how many in inventory
    quantity = int(request.form.get('quantity', 1))  #how many the user wants
    iq = invt - quantity#subtract the two

    item = next((item for item in session['cart'] if item['id'] == product_id), None)
    product = next((item for item in catalog if item[0] == product_id), None)
    if iq > -1: #makes sure we cant pull more than what is available, 
        if product: #if the product exists and item ecists we add more to it if possible
            if item:
                qty = item['quantity'] + quantity 
                niq = invt - qty
                if niq > -1:
                    item['quantity'] = item['quantity']+ quantity
                    item['inventory'] = niq
            else:#product is not in the cart so we put it in the cart
                cart_item = {'id': product[0], 'name': product[1], 'price': product[2], 'weight':product[3], 'quantity': quantity, 'inventory':iq}
                session['cart'].append(cart_item)
            session.modified = True
    return redirect(url_for('cat'))
#removes the item from the cart
@app.route('/remove_from_cart/<int:product_id>')
def remove_from_cart(product_id):
    session['cart'] = [item for item in session['cart'] if item['id'] != product_id]
    session.modified = True
    return redirect(url_for('cat'))
#updates the cart with a new quantity
@app.route('/update_cart/<int:product_id>', methods=['POST'])
def update_cart(product_id):
    catalog = get_products()
    new_quantity = int(request.form.get('quantity', 1))  #the quantity to be added
    product = next((item for item in catalog if item[0] == product_id), None) #gets the correct product id in the cart 
    invt = product[5] #gets inventory
    iq = invt - new_quantity #gets the difference of quantity from user and inventory
    for item in session['cart']:
        if iq > -1:#is the update possible? sets new quantity if so
            if item['id'] == product_id:
                item['quantity'] = new_quantity
                item['inventory'] = iq
                session.modified = True
                break
    return redirect(url_for('cat'))
#test thing not used
@app.route('/update_scart/<int:product_id>', methods=['POST'])
def update_scart(product_id):
    new_quantity = int(request.form.get('quantity', 1))  # Default to 1 if quantity is not provided
    #iq = invt - new_quantity
    for item in session['cart']:
        iq = item['inventory'] - new_quantity
        if iq > -1:
            if item['id'] == product_id:
                item['quantity'] = new_quantity
                item['inventory'] = iq
                session.modified = True
                break
    return redirect(url_for('view_cart'))
#cart holds all the items and the detail associated with the item
@app.route('/cart')
def view_cart():
    #first chunk sets vars to 0 and gets nums for price calculation
    total_price = 0
    fee = 0
    sum_price=0
    total_chaunk=0
    chaunkCur = db.cursor()
    chaunkCur.execute("select * from shippinghandlingcharges")
    fees = chaunkCur.fetchall()

    #goes through and cart and totals all of the data associated with price
    for item in session['cart']:
        sum_price = sum_price + (float(item['price']) * float(item['quantity']))
        total_chaunk = total_chaunk + (float(item['weight']) * float(item['quantity']))
        for chunk in fees:
            fee = chunk[1]
            if total_chaunk < chunk[0]:
                break
    total_price = sum_price
    order_price = sum_price + float(fee)

    return render_template('cart.html', cart=session['cart'],order_price=round(order_price,2), total_fees=round(fee,2),total_price=round(total_price,2),total_chaunk=round(total_chaunk,2) )

#an amalgamation of code but it gets all of the data needed to let the user know the info and the warehouse to recieve the right order
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    #if request.method == 'GET';
    #gets all the data for orders and price
    fname = request.form['fname']
    lname = request.form['lname']
    addr = request.form['addr']
    cty = request.form['cty']
    state = request.form['state']
    zip = request.form['zip']
    email = request.form['email']
    CCN = request.form['CCN']
    CCNExp = request.form['CCNExp']
    tprice = request.form['tprice']
    oprice = request.form['oprice']
    tchaunk = request.form['tchaunk']
    tfees = request.form['tfees']
    chCur = db.cursor()
    fullname = fname + ' ' + lname
    orderID = random.randint(1000, 9999999)
    result = authorize_cc('VE001-89', orderID, CCN, fullname, CCNExp, oprice )

    #gets ready to send the appropiate response to the user
    response = result
    responsemsg = result.json()
    authcode = responsemsg.get('authorization')
    ecode = responsemsg.get('errors')

    #200 means that the request has successfully completed meaning we can set up order information
    #authcode means we can proceed, and we get all the data for order details, we join the columns into a query and execute
    #execute order query, execute orderdetail query, change inventory data
    if (response.status_code == 200):
        if authcode:
            dtime = date.today()
            columns = (
            'order_id', 'fname', 'lname', 'email', 'mailing_street', 'mailing_city', 'mailing_state', 'mailing_zip',
            'order_date', 'credit_card_number', 'credit_card_expiration_date', 'authorization_number', 'total_price',
            'order_total', 'status', 'weight','shipping_handling_charge' )

            values = (orderID, fname, lname, email,addr,cty,state,zip, dtime, CCN, CCNExp, authcode,tprice,oprice,'Open', tchaunk, tfees)
            insert_query = f"INSERT INTO orders ({', '.join(columns)}) VALUES ({', '.join(['%s' for _ in range(len(values))])})"
            #insert_query = """INSERT INTO orders (order_id,fname,lname,email,credit_card_number,credit_card_expiration_date) VALUES (%s,%s,%s,%s,%s,%s)"""
            chCur.execute(insert_query, values)
            db.commit()
            for item in session['cart']:
                columns = ('order_id', 'part_number', 'descr', 'price', 'quantity_ordered')
                prodid = (int(item['id']))
                fprice = (float(item['price']))
                cprice = round(fprice,2)
                qty = int(item['quantity'])
                values = ( orderID, prodid, item['name'], cprice,qty )
                insert_query = f"INSERT INTO OrderDetails ({', '.join(columns)}) VALUES ({', '.join(['%s' for _ in range(len(values))])})"
                chCur.execute(insert_query, values)
                db.commit()
                chCur.execute("select quantity_on_hand from inventory where part_number = %s", (prodid,) )
                idata = chCur.fetchone()
                for ilist in idata:
                    qoh = ilist
                    qoh = qoh - qty
                    chCur.execute("update inventory set quantity_on_hand = %s where part_number = %s",(qoh,prodid ))
                    db.commit()
            chCur.close()
            print(response.text)
        else:
            print(ecode)
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
    session.pop('cart',None)#clears cart to make it empty
    ovalues = {'id': orderID, 'fname': fname, 'lname': lname, 'price': tprice, 'authcode': authcode}
    #session['orders'].append(ovalues)
    return render_template('/OrderComplete.html', ordID = orderID, name = fname +" "+lname, price=oprice, acode=authcode )

#once the checkout has been made user is sent here to say order complete
@app.route('/OrdComp', methods=['GET', 'POST'])
def ord_comp():
    return render_template('/OrderComplete.html' )

@app.route('/warehouse')
def warehouse():
    # Retrieve order history from the database
    cursor.execute("SELECT * FROM Orders where status = %s", ('Open',))
    orders = cursor.fetchall()
    for crack in orders:
        print(crack)
    return render_template('warehouse.html', orders=orders)

@app.route('/ship/<int:order_id>', methods=['POST'])
def ship(order_id):
    chCur = db.cursor()
    # Retrieve order history from the database
    #cursor.execute("SELECT Orders.*, o.* FROM Orders inner join orderdetails o  ON Orders.order_id =o.order_id")
    cursor.execute("SELECT * FROM Orders where order_id = %s", (order_id,))
    orders = cursor.fetchone()
    chCur.execute("SELECT * FROM orderdetails where order_id = %s", (order_id,))
    orddeets = chCur.fetchall()
    for crack in orders:
        print(crack)
    chCur.close()
    return render_template('Ship.html', orders=orders, orddeets = orddeets)

@app.route('/ship_update/<int:order_id>', methods=['POST'])
def ship_update(order_id):
    chCur = db.cursor()
    # Retrieve order history from the database
    #cursor.execute("SELECT Orders.*, o.* FROM Orders inner join orderdetails o  ON Orders.order_id =o.order_id")
    chCur.execute("update Orders set Status = %s where order_id = %s", ('Closed', order_id))
    db.commit()
    return redirect(url_for('warehouse'))

if __name__ == '__main__':
    app.run(debug=True)
