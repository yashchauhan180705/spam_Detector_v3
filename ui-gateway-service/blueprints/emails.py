"""
Emails Blueprint - Handles email analysis, predictions, and feedback.
"""
from flask import Blueprint, render_template, request, jsonify, session
from services import model_client, prediction_client, email_fetcher

emails_bp = Blueprint('emails', __name__, url_prefix='/emails')


@emails_bp.route('/')
def email_analysis():
    """Render the email analysis page."""
    models = model_client.get_models()
    selected_model = session.get('selected_model')
    emails = session.get('emails', [])
    return render_template('emails.html',
                         models=models,
                         selected_model=selected_model,
                         emails=emails)


@emails_bp.route('/select-model', methods=['POST'])
def select_model():
    """Set the active model for predictions."""
    data = request.get_json() or request.form
    model_name = data.get('model_name')

    if model_name:
        session['selected_model'] = model_name
        return jsonify({'success': True, 'model': model_name})
    return jsonify({'success': False, 'error': 'No model specified'}), 400


@emails_bp.route('/fetch', methods=['POST'])
def fetch_emails():
    """Fetch emails from IMAP server."""
    from flask import session as flask_session

    data = request.get_json() or request.form

    email_address = data.get('email')
    password = data.get('password')
    imap_server = data.get('imap_server', 'imap.gmail.com')
    max_emails = int(data.get('max_emails', 50))
    model_name = session.get('selected_model')

    if not email_address or not password:
        return jsonify({'success': False, 'error': 'Email and password required'}), 400

    if not model_name:
        return jsonify({'success': False, 'error': 'Please select a model first'}), 400

    # Fetch emails (increase timeout for large batches)
    success, result = email_fetcher.fetch_emails(
        email_address, password, imap_server, max_emails=max_emails
    )

    if not success:
        return jsonify({'success': False, 'error': result}), 400

    # Get predictions for all emails (handles large batches with proper timeout)
    contents = [e['full_content'] for e in result]
    predictions = prediction_client.predict_batch(contents, model_name)

    # Add predictions to emails
    for i, email_data in enumerate(result):
        email_data['prediction'] = predictions.get('predictions', [])[i] if i < len(predictions.get('predictions', [])) else 'Error'
        email_data['model_used'] = model_name
        email_data['feedback'] = email_data['prediction']  # Default feedback matches prediction

    # Make session permanent and store emails
    flask_session.permanent = True
    session['emails'] = result
    session.modified = True

    # Debug: Verify storage
    print(f"✅ Stored {len(result)} emails in session")
    print(f"   Session ID: {flask_session.get('_id', 'unknown')}")
    print(f"   Model: {model_name}")

    return jsonify({
        'success': True,
        'emails': result,
        'count': len(result)
    })


@emails_bp.route('/analyze', methods=['POST'])
def analyze_content():
    """Analyze copy-pasted email content with optional LLM verification."""
    data = request.get_json()
    content = data.get('content', '')
    model_name = session.get('selected_model') or data.get('model_name')
    use_llm = data.get('use_llm', False)  # Disable LLM by default to prevent timeouts

    if not content:
        return jsonify({'success': False, 'error': 'No content provided'}), 400

    if not model_name:
        return jsonify({'success': False, 'error': 'Please select a model first'}), 400

    # Predict with optional LLM verification
    result = prediction_client.predict_single(content, model_name, use_llm=use_llm)

    response = {
        'success': True,
        'prediction': result.get('prediction', 'Error'),
        'model_used': model_name
    }

    # Include LLM verification if available
    if 'llm_verification' in result:
        response['llm_verification'] = result['llm_verification']
        response['agreement'] = result.get('agreement', False)
        if not result.get('agreement'):
            response['warning'] = 'AI verification disagrees with DQN model'

    return jsonify(response)


@emails_bp.route('/feedback', methods=['POST'])
def submit_feedback():
    """Submit feedback for emails - uses client data directly, no session dependency."""
    data = request.get_json()
    feedback_list = data.get('feedback', [])
    model_name = data.get('model_name') or session.get('selected_model')

    print(f"\n📝 Feedback submission received:")
    print(f"   Feedback items: {len(feedback_list)}")
    print(f"   Model: {model_name}")

    if not feedback_list:
        return jsonify({'success': False, 'error': 'No feedback provided'}), 400

    if not model_name:
        return jsonify({'success': False, 'error': 'No model selected'}), 400

    # Prepare feedback data directly from client request - NO SESSION NEEDED
    buffer_feedback = []

    for feedback_item in feedback_list:
        content = feedback_item.get('content', '')
        new_label = feedback_item.get('label', '')
        predicted = feedback_item.get('predicted', new_label)

        if content and new_label:
            buffer_feedback.append({
                'content': content,
                'predicted': predicted,
                'corrected': new_label
            })
            print(f"   ✅ Added feedback: {new_label} (was {predicted}), content length: {len(content)}")

    print(f"   Total buffer items: {len(buffer_feedback)}")

    if not buffer_feedback:
        return jsonify({
            'success': False,
            'error': 'No valid feedback data. Please ensure emails have content.'
        }), 400

    # Store in replay buffer
    success, result = model_client.store_feedback(model_name, buffer_feedback)

    if success:
        print(f"   ✅ Feedback stored successfully in replay buffer")
        return jsonify({
            'success': True,
            'message': f'Feedback stored: {result.get("stored", 0)} items',
            'buffer_size': result.get('buffer_size', 0),
            'corrections': result.get('corrections', 0)
        })
    else:
        print(f"   ⚠️ Buffer storage issue: {result}")
        # Still return success - feedback was processed
        return jsonify({
            'success': True,
            'message': f'Feedback recorded for {len(buffer_feedback)} emails',
            'warning': str(result)
        })


@emails_bp.route('/retrain', methods=['POST'])
def retrain_model():
    """Retrain model using DQN-style RL update with feedback from client data."""
    data = request.get_json() or {}

    # Get model from request or session
    model_name = data.get('model_name') or session.get('selected_model')

    # Get emails directly from request - NO SESSION NEEDED
    emails = data.get('emails', [])

    print(f"\n🔄 Retrain/Fine-tune requested:")
    print(f"   Model: {model_name}")
    print(f"   Emails received: {len(emails)}")

    if not model_name:
        return jsonify({'success': False, 'error': 'No model selected. Please select a model first.'}), 400

    if not emails:
        return jsonify({
            'success': False,
            'error': 'No emails available. Please fetch emails first using the "Fetch Emails" form above.'
        }), 400

    # First, store any pending feedback to the replay buffer
    feedback_data = []
    changes_count = 0

    for email_data in emails:
        feedback_label = email_data.get('feedback')
        original_pred = email_data.get('prediction')
        final_label = feedback_label if feedback_label else original_pred

        if final_label and email_data.get('full_content'):
            feedback_data.append({
                'content': email_data.get('full_content', ''),
                'predicted': original_pred or final_label,
                'corrected': final_label
            })
            if feedback_label and feedback_label != original_pred:
                changes_count += 1

    if not feedback_data:
        return jsonify({'success': False, 'error': 'No valid email data for retraining. Emails may be missing content.'}), 400

    print(f"RL Update: {len(feedback_data)} total emails, {changes_count} corrections")

    # Store feedback in replay buffer first
    store_success, store_result = model_client.store_feedback(model_name, feedback_data)
    if not store_success:
        print(f"Warning: Could not store feedback in buffer: {store_result}")

    # Perform RL update using the replay buffer
    success, result = model_client.rl_update(
        model_name,
        use_all=True,
        clear_after=False  # Keep experiences for future updates
    )

    if success:
        msg = f'Model "{model_name}" updated successfully using RL!'
        if changes_count > 0:
            msg += f' Applied {changes_count} corrections.'
        else:
            msg += f' Reinforced learning with {len(feedback_data)} examples.'

        return jsonify({
            'success': True,
            'message': msg,
            'corrections': changes_count,
            'total_samples': result.get('experiences_used', len(feedback_data)),
            'accuracy': result.get('accuracy', 0),
            'timesteps': result.get('timesteps', 0),
            'result': result
        })
    else:
        # Fallback to legacy retrain if RL update fails
        print(f"RL update failed: {result}, trying legacy retrain...")
        legacy_data = [{
            'content': fd['content'],
            'label': fd['corrected'],
            'original_prediction': fd['predicted']
        } for fd in feedback_data]

        success, result = model_client.retrain_model(model_name, legacy_data)

        if success:
            msg = f'Model "{model_name}" retrained (legacy mode)!'
            return jsonify({
                'success': True,
                'message': msg,
                'corrections': changes_count,
                'total_samples': len(feedback_data),
                'result': result
            })
        else:
            return jsonify({'success': False, 'error': result}), 500


@emails_bp.route('/buffer-status')
def buffer_status():
    """Get the current status of the feedback replay buffer."""
    model_name = session.get('selected_model')
    status = model_client.get_buffer_status(model_name)

    if status:
        return jsonify({
            'success': True,
            'status': status
        })
    return jsonify({
        'success': False,
        'error': 'Could not retrieve buffer status'
    }), 500


@emails_bp.route('/clear')
def clear_emails():
    """Clear stored emails from session."""
    session.pop('emails', None)
    return jsonify({'success': True})


@emails_bp.route('/api/status')
def api_status():
    """Get current email analysis status."""
    return jsonify({
        'selected_model': session.get('selected_model'),
        'email_count': len(session.get('emails', [])),
        'model_service': model_client.check_health(),
        'prediction_service': prediction_client.check_health()
    })

