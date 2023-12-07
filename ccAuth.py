import requests

def authorize_cc(vendor, trans_num, cc_num, name, exp, curr_amnt):
    url = 'http://blitz.cs.niu.edu/CreditCard/'
    jsonsend = {'vendor': vendor, 'trans': trans_num, 'cc': cc_num, 'name': name, 'exp': exp, 'amount': curr_amnt}
    result = requests.post(url, json=jsonsend)
    return result