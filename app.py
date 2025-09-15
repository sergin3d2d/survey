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

texts = ["Mental Demand — How much thinking, deciding, or remembering was required.",
         "Physical Demand — How much physical activity or movement was required.",
         "Temporal Demand — How hurried or rushed you felt.",
         "Performance — How well you felt you did overall.",
         "Effort — How hard you had to work (mentally or physically) to reach your performance.",
         "Frustration — How insecure, discouraged, irritated, or stressed you felt."]
left_labels = ["Very Low", "Very Low", "Very Low", "Excellent", "Very Low", "Very Low"]
right_labels = ["Very High", "Very High", "Very High", "Poor", "Very High", "Very High"]
pairs = list(itertools.combinations(range(len(texts)), 2))

@app.route('/')
def index():
    session.clear()
    return render_template('initial_conditions.html')


@app.route('/initialize_experiment', methods=['POST'])
def initialize_experiment():
    # Save initial conditions to session
    session['participant_id'] = request.form.get('participant_id')
    session['vision_test_score'] = request.form.get('vision_test_score')
    session['ipd'] = request.form.get('ipd')
    session['dominant_hand'] = request.form.get('dominant_hand')
    session['previous_ar_experience'] = request.form.get('previous_ar_experience')
    
    # Also, store them in a dictionary for easy saving later
    session['initial_conditions_responses'] = {
        'participant_id': request.form.get('participant_id'),
        'vision_test_score': request.form.get('vision_test_score'),
        'ipd': request.form.get('ipd'),
        'dominant_hand': request.form.get('dominant_hand'),
        'previous_ar_experience': request.form.get('previous_ar_experience')
    }
    
    config = load_config()
    main_conditions = config['main_conditions']
    random.shuffle(main_conditions)
    session['main_conditions_randomized'] = main_conditions
    
    return render_template('initialization_summary.html', 
                           conditions=main_conditions, 
                           ipd=session['ipd'], 
                           dominant_hand=session['dominant_hand'])


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
    # If at the beginning of the questionnaire, go back to the initial page
    if 'main_conditions_randomized' in session:
        return redirect(url_for('index')) 
    return redirect(url_for('index'))




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
