from flask import Flask, render_template, request, redirect, url_for, session
import itertools

app = Flask(__name__)
app.secret_key = 'super secret key'

## Texts for the individual questionnaire items
texts = ["Mental Demand - How mentally demanding was the task?",
         "Physical Demand - How physically demanding was the task?",
         "Temporal Demand - How hurried or rushed was the pace of the task?",
         "Performance - How successful were you in accomplishing what you were asked to do?",
         "Effort - How hard did you have to work to accomplish your level of performance?",
         "Frustration - How insecure, discouraged, irritated, stressed and annoyed were you?"]

## Labels on the left and right sides of the scale
left_labels = ["Very Low", "Very Low", "Very Low", "Perfect", "Very Low", "Very Low"]
right_labels = ["Very High", "Very High", "Very High", "Failure", "Very High", "Very High"]

## Labels of the Conditions to be chosen from
conditions = ["Condition 1", "Condition 2"]

## Experiments to be chosen from
experiments = ["Experiment 1", "Experiment 2"]

pairs = list(itertools.combinations(range(len(texts)), 2))

@app.route('/')
def index():
    step = request.args.get('step', '1')
    if step == '1':
        session.clear()
    return render_template('index.html',
                           texts=texts,
                           left_labels=left_labels,
                           right_labels=right_labels,
                           conditions=conditions,
                           experiments=experiments,
                           step=step,
                           pairs=pairs)

@app.route('/submit', methods=['POST'])
def submit():
    step = request.form.get('step')

    if step == '1':
        session['experiment'] = request.form['experiment']
        session['user_id'] = request.form['user_id']
        session['condition'] = request.form['condition']
        session['ratings'] = [request.form.get('q' + str(i)) for i in range(len(texts))]
        return redirect(url_for('index', step='2'))

    elif step == '2':
        weights = [0] * len(texts)
        for i in range(len(pairs)):
            winner = int(request.form.get('pair_' + str(i)))
            weights[winner] += 1

        write_string = ''
        write_string += session['experiment'] + ','
        write_string += session['user_id'] + ','
        write_string += session['condition']

        for rating in session['ratings']:
            write_string += ',' + str(rating)

        weighted_score = 0
        for i in range(len(texts)):
            weighted_score += int(session['ratings'][i]) * weights[i]
        
        write_string += ',' + str(weighted_score / 15)


        with open("nasa-tlx-results.txt", "a") as f:
            f.write(write_string + '\n')

        return "The results were written successfully."

if __name__ == '__main__':
    app.run(debug=True, port=5001)
