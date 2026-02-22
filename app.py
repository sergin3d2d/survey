from flask import Flask, render_template, request, redirect, url_for, session
import itertools
import json
import os
import csv
from datetime import datetime
import random

app = Flask(__name__)
app.secret_key = 'super secret key'
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True only if using HTTPS

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

@app.context_processor
def inject_global_settings():
    config = load_config()
    return dict(
        question_font_size=config.get('question_font_size', 1.6),
        description_font_size=config.get('description_font_size', 1.4),
        global_font_size=config.get('global_font_size', 1.0)
    )

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
    session['user_id'] = f"user_{datetime.now().strftime('%Y%m%d%H%M%S')}"
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
        'responses': session.get('initial_conditions_responses', {})
    })
    session.pop('initial_conditions_responses', None) # Clear it after saving

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
        
        if 'responses' not in session:
            session['responses'] = {}
        session['responses'][current_task] = responses
        
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
        current_responses = session.get('responses', {}).get(current_task, {})
        return render_template('nasa_tlx.html', texts=texts, left_labels=left_labels, right_labels=right_labels, condition=current_task, existing_responses=current_responses, participant_id=session.get('participant_id'))
    elif current_task.startswith('PCUE-Q'):
        current_responses = session.get('responses', {}).get(current_task, {})
        return render_template('pcueq.html', condition=current_task, existing_responses=current_responses, participant_id=session.get('participant_id'))
    elif current_task == "Final Preference":
        current_responses = session.get('responses', {}).get(current_task, {})
        return render_template('final_preference.html', conditions=session.get('main_conditions_randomized', []), existing_responses=current_responses, participant_id=session.get('participant_id'))
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
        
        if 'responses' not in session:
            session['responses'] = {}
        if current_condition not in session['responses']:
            session['responses'][current_condition] = {}
        session['responses'][current_condition]['weights'] = weights

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

    existing_weights = session.get('responses', {}).get(current_condition, {}).get('weights', [])
    return render_template('nasa_tlx_weighting.html', pairs=pairs, texts=texts, condition=current_condition, existing_weights=existing_weights, participant_id=session.get('participant_id'))

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
        config['question_font_size'] = float(request.form.get('question_font_size', 1.6))
        config['description_font_size'] = float(request.form.get('description_font_size', 1.4))
        config['global_font_size'] = float(request.form.get('global_font_size', 1.0))
        save_config(config)
        return redirect(url_for('index'))
        
    return render_template('settings.html', 
                            main_conditions=config.get('main_conditions', []),
                            weighted=config.get('weighted', True),
                            question_font_size=config.get('question_font_size', 1.6),
                            description_font_size=config.get('description_font_size', 1.4),
                            global_font_size=config.get('global_font_size', 1.0))

@app.route('/review')
def review():
    grouped_results = {}
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                uid = row.get('user_id', 'N/A')
                if uid not in grouped_results:
                    grouped_results[uid] = {
                        'participant_id': 'N/A',
                        'timestamp': row['timestamp'],
                        'sections': {}
                    }
                
                q_type = row['questionnaire']
                cond = row['condition']
                
                if q_type == 'pre_experiment' and row['key'] == 'participant_id':
                    grouped_results[uid]['participant_id'] = row['value']

                section_key = f"{q_type} | {cond}"
                if section_key not in grouped_results[uid]['sections']:
                    grouped_results[uid]['sections'][section_key] = []
                
                grouped_results[uid]['sections'][section_key].append({
                    'key': row['key'],
                    'value': row['value']
                })

    # Sort participants by timestamp descending
    sorted_uids = sorted(grouped_results.keys(), key=lambda x: grouped_results[x]['timestamp'], reverse=True)
    
    return render_template('review.html', grouped_results=grouped_results, sorted_uids=sorted_uids)

if __name__ == '__main__':
    # Set host to '0.0.0.0' to allow access from other devices on the same network

    app.run(debug=True, port=5001, host='0.0.0.0', ssl_context='adhoc')
