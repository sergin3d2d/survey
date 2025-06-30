from flask import Flask, render_template, request, redirect, url_for, session
import itertools
import json
import os
import csv
from datetime import datetime
import random

app = Flask(__name__)
app.secret_key = 'super secret key'

CONFIG_FILE = 'config.json'
RESULTS_FILE = 'results.csv'

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {
        'main_conditions': ['On-Screen', 'AR-OST', 'AR-VST'],
        'weighted': True
    }

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

def write_result(data):
    with open(RESULTS_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        if f.tell() == 0:
            writer.writerow(['timestamp', 'user_id', 'questionnaire', 'condition', 'key', 'value'])
        
        timestamp = datetime.now().isoformat()
        user_id = session.get('user_id', 'N/A')
        questionnaire = data.get('questionnaire', 'N/A')
        condition = data.get('condition', 'N/A')

        for key, value in data.get('responses', {}).items():
            writer.writerow([timestamp, user_id, questionnaire, condition, key, value])

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

texts = ["Mental Demand - How mentally demanding was the task?",
         "Physical Demand - How physically demanding was the task?",
         "Temporal Demand - How hurried or rushed was the pace of the task?",
         "Performance - How successful were you in accomplishing what you were asked to do?",
         "Effort - How hard did you have to work to accomplish your level of performance?",
         "Frustration - How insecure, discouraged, irritated, stressed and annoyed were you?"]
left_labels = ["Very Low", "Very Low", "Very Low", "Perfect", "Very Low", "Very Low"]
right_labels = ["Very High", "Very High", "Very High", "Failure", "Very High", "Very High"]
pairs = list(itertools.combinations(range(len(texts)), 2))

@app.route('/')
def index():
    session.clear()
    config = load_config()
    session['user_id'] = f'user_{datetime.now().strftime("%Y%m%d%H%M%S")}'
    return render_template('pre_experiment.html', conditions=config['main_conditions'])

@app.route('/check_eligibility', methods=['POST'])
def check_eligibility():
    config = load_config()
    responses = request.form.to_dict()
    
    session['participant_id'] = responses.get('participant_id')
    session['vision_test_score'] = responses.get('vision_test_score')
    session['ipd'] = responses.get('ipd')
    
    # Store all pre-experiment responses for saving
    session['pre_experiment_responses'] = responses

    eligibility = {
        'consent': responses.get('consent') == 'Yes',
        'no_motor_impairments': responses.get('motor_impairments') == 'No',
        'no_health_issues': responses.get('health_issues') == 'No'
    }
    
    is_eligible = all(eligibility.values())

    if is_eligible:
        main_conditions = config['main_conditions']
        random.shuffle(main_conditions)
        session['main_conditions_randomized'] = main_conditions
    
    return render_template('eligibility_check.html', eligibility=eligibility, is_eligible=is_eligible)

@app.route('/start_experiment_proper', methods=['POST'])
def start_experiment_proper():
    config = load_config()
    
    # Write pre-experiment data
    write_result({
        'questionnaire': 'pre_experiment',
        'condition': 'Pre-Experiment',
        'responses': session.get('pre_experiment_responses', {})
    })
    session.pop('pre_experiment_responses', None) # Clear it after saving

    workflow = []
    for condition in session['main_conditions_randomized']:
        workflow.append(condition)
        workflow.append(f"PCUE-Q for {condition}")
    workflow.append("Final Preference")
    
    session['workflow'] = workflow
    session['current_step'] = 0
    return redirect(url_for('questionnaire'))


@app.route('/questionnaire', methods=['GET', 'POST'])
def questionnaire():
    if 'workflow' not in session or session['current_step'] >= len(session['workflow']):
        return render_template('end.html')

    current_task = session['workflow'][session['current_step']]
    config = load_config()

    if request.method == 'POST':
        responses = request.form.to_dict()
        questionnaire_type = responses.pop('questionnaire_type', 'unknown')
        
        write_result({
            'questionnaire': questionnaire_type,
            'condition': current_task,
            'responses': responses
        })

        if questionnaire_type == 'nasa_tlx' and config['weighted']:
            session['nasa_tlx_ratings'] = {k: v for k, v in responses.items() if k.startswith('q')}
            return redirect(url_for('nasa_tlx_weighting'))

        session['current_step'] += 1
        return redirect(url_for('questionnaire'))

    if current_task in config['main_conditions']:
        return render_template('nasa_tlx.html', texts=texts, left_labels=left_labels, right_labels=right_labels, condition=current_task)
    elif current_task.startswith('PCUE-Q'):
        return render_template('pcueq.html', condition=current_task)
    elif current_task == "Final Preference":
        return render_template('final_preference.html', conditions=session.get('main_conditions_randomized', []))
    else:
        return f"Unknown task: {current_task}"

@app.route('/nasa_tlx_weighting', methods=['GET', 'POST'])
def nasa_tlx_weighting():
    # This route is now implicitly part of the main questionnaire flow
    # but we need to handle the step increment correctly.
    # The logic to call this is inside the questionnaire POST handler.
    
    # Find the current main condition based on the workflow
    current_condition = "Unknown"
    for task in reversed(session['workflow'][:session['current_step']+1]):
        if task in session['main_conditions_randomized']:
            current_condition = task
            break

    if request.method == 'POST':
        weights = [0] * len(texts)
        for i in range(len(pairs)):
            winner = int(request.form.get('pair_' + str(i)))
            weights[winner] += 1
        
        ratings = session.get('nasa_tlx_ratings', {})
        weighted_score = 0
        for i in range(len(texts)):
            weighted_score += int(ratings.get(f'q{i}', 0)) * weights[i]
        
        write_result({
            'questionnaire': 'nasa_tlx_weighted_score',
            'condition': current_condition,
            'responses': {'weighted_score': weighted_score / 15}
        })

        session.pop('nasa_tlx_ratings', None)
        session['current_step'] += 1
        return redirect(url_for('questionnaire'))

    return render_template('nasa_tlx_weighting.html', pairs=pairs, texts=texts, condition=current_condition)

@app.route('/back')
def back():
    if 'current_step' in session and session['current_step'] > 0:
        session['current_step'] -= 1
        return redirect(url_for('questionnaire'))
    # If at the beginning of the questionnaire, go back to eligibility check
    if 'main_conditions_randomized' in session:
        return redirect(url_for('check_eligibility_page')) # A new route to re-render the check page
    return redirect(url_for('index'))

@app.route('/check_eligibility_page')
def check_eligibility_page():
    # This route helps the back button work from the first questionnaire
    eligibility = {
        'consent': session.get('pre_experiment_responses', {}).get('consent') == 'Yes',
        'no_motor_impairments': session.get('pre_experiment_responses', {}).get('motor_impairments') == 'No',
        'no_health_issues': session.get('pre_experiment_responses', {}).get('health_issues') == 'No'
    }
    return render_template('eligibility_check.html', eligibility=eligibility)


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    config = load_config()
    if request.method == 'POST':
        config['main_conditions'] = [c.strip() for c in request.form['main_conditions'].split('\n') if c.strip()]
        config['weighted'] = 'weighted' in request.form
        save_config(config)
        return redirect(url_for('index'))
        
    return render_template('settings.html', 
                           main_conditions=config.get('main_conditions', []),
                           weighted=config.get('weighted', True))

if __name__ == '__main__':
    app.run(debug=True, port=5001)
