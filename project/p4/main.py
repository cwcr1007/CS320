# project: p4
# submitter: zdai38
# partner: none

# COVID-19 State Data
# We can create a histogram about the data.
# Scource: https://www.kaggle.com/nightranger77/covid19-state-data?select=COVID19_state.csv

import pandas as pd
from flask import Flask, request, jsonify
import re

app = Flask(__name__)
df = pd.read_csv("main.csv")

visit = 0
@app.route('/')
def home():
    global visit
    visit += 1
    with open("index.html") as f:
        html_A = f.read()
    html_B = html_A.replace('<p><a href="donate.html?from=A" style="background-color: red;">Donation</a></p>', '<p><a href="donate.html?from=B" style="background-color: yellow;">Donation</a></p>')
    
    if visit <= 10:
        if visit%2 ==1: # test A:
            return html_A
        if visit%2 ==0: # test B:
            return html_B
    else: 
        if count_A > count_B:
            return html_A
        else:
            return html_B

@app.route('/browse.html')
def show_table():
    table = "<h1>{}</h1>".format("Browse") + df.to_html()
    return table

count = 0
@app.route('/email', methods=["POST"])
def email():
    email = str(request.data, "utf-8")
    if re.match(r"\w+@\w+\.\w+", email): # 1
        global count
        count += 1
        with open("emails.txt", "a") as f: # open file in append mode
            f.write(email + "\n") # 2
        return jsonify("thanks, you're subscriber number {}!".format(count))
    return jsonify("Bob reminds you: please confirm email address and try again.") # 3

count_A = 0
count_B = 0
@app.route('/donate.html')
def donate():
    global count_A
    global count_B
    letter = request.args.get("from")
    if letter == "A":
        count_A += 1
    if letter == "B":
        count_B += 1      
    text = "<h1>{}</h1>".format("Donation") + "<body><p>{}</p></body>".format("We're a non-profit that depends on donations to stay online and thriving. If everyone who reads our website gave just a little, we could keep it thriving for years to come. The price of a cup of coffee is all we ask.") + "<body><p>{}</p></body>".format("Thanks,") + "<body><p>{}</p></body>".format("Bob Dai (Website Founder)") 
    return text

@app.route('/api.html')
def api_funcion():
    with open("api.html") as f:
        html = f.read()
    return html


@app.route('/covid.json')
def covid():
    input = request.args.get("state")
    print(input)
    df_list = df.to_dict('records')
    
    for i in df_list:
        if i["State"] == input:
            for idx in range(len(df_list)):
                if df_list[idx] == i:
                    return jsonify([[idx ,i]])
    return jsonify(df_list)


@app.route('/covidcols.json')
def covidcols():
    d = {}
    for i in df.dtypes.index:
        for j in df.dtypes:
            d[i] = str(j)
            
    return jsonify(d)


if __name__ == '__main__':
    app.run(host="0.0.0.0") # don't change this line!