from flask import Flask, render_template, g, request
from datetime import datetime
from database import get_db, connect_db

app = Flask(__name__)


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


@app.route('/', methods=['GET', 'POST'])
def index():
    db = get_db()
    if request.method == 'POST':
        date = request.form['new-day']
        dt = datetime.strptime(date, '%Y-%m-%d')
        database_date = datetime.strftime(dt, '%Y%m%d')

        db.execute('insert into log_date (entry_date) values(?)',
                   [database_date])
        db.commit()

    cur = db.execute('''select entry_date, sum(food.protein) as total_protein, 
                     sum(food.carbohydrates) as total_carbohydrates, sum(food.fat) as total_fat,
                     sum(food.calories) as total_calories 
                     from log_date left join food_date on log_date.id = food_date.log_date_id 
                     left join food on food.id = food_date.food_id 
                     group by log_date.id order by log_date.entry_date''')

    results = cur.fetchall()

    dates = []

    for i in results:
        single_date = {}

        single_date['protein'] = i['total_protein']
        single_date['carbohydrates'] = i['total_carbohydrates']
        single_date['fat'] = i['total_fat']
        single_date['calories'] = i['total_calories']

        d = datetime.strptime(str(i['entry_date']), '%Y%m%d')
        single_date['link_date'] = str(i['entry_date'])
        single_date['entry_date'] = datetime.strftime(d, '%B %d, %Y')
        dates.append(single_date)

    return render_template('home.html', dates=dates)


@app.route('/view/<date>', methods=['GET', 'POST'])
def view(date):
    db = get_db()
    cur = db.execute('select * from log_date where entry_date = ?', [date])
    date_result = cur.fetchone()
    food_cur = db.execute('select id, name from food')
    foods = food_cur.fetchall()

    if request.method == 'POST':
        food_id = request.form['selected_food']
        db.execute('insert into food_date(food_id, log_date_id) values (?,?)', [
                   food_id, date_result['id']])
        db.commit()

    d = datetime.strptime(str(date_result['entry_date']), '%Y%m%d')
    pretty_date = datetime.strftime(d, '%B %d, %Y')

    log_cur = db.execute('''select food.name,food.protein, food.carbohydrates, food.fat, food.calories 
                         from log_date join food_date on log_date.id = food_date.log_date_id 
                         join food on food.id = food_date.food_id 
                         where log_date.entry_date = ?''', [date])

    log_results = log_cur.fetchall()

    total_values = {}
    total_values['protein'] = 0
    total_values['carbohydrates'] = 0
    total_values['fat'] = 0
    total_values['calories'] = 0

    for log in log_results:
        total_values['protein'] += log['protein']
        total_values['carbohydrates'] += log['carbohydrates']
        total_values['fat'] += log['fat']
        total_values['calories'] += log['calories']

    return render_template('day.html', date=date, pretty_date=pretty_date, foods=foods, log_results=log_results, total_values=total_values)


@app.route('/food', methods=['GET', 'POST'])
def food():
    db = get_db()
    if request.method == 'POST':
        name = request.form['food-name']
        protein = int(request.form['protein'])
        carbohydrates = int(request.form['carbohydrates'])
        fat = int(request.form['fat'])

        calories = calculate_calory(protein, carbohydrates, fat)

        db.execute('insert into food (name, protein, carbohydrates, fat, calories) values(?,?,?,?,?)',
                   [name, protein, carbohydrates, fat, calories])
        db.commit()

    cur = db.execute(
        'select name, protein, carbohydrates, fat, calories from food')
    foods = cur.fetchall()

    return render_template('add_food.html', foods=foods)


def calculate_calory(protein: int, carbohydrates: int, fat: int):
    return protein * 4 + carbohydrates * 4 + fat * 9


if __name__ == '__main__':
    app.run(debug=True)
