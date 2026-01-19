"""
Models Blueprint - Handles model management operations.
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
import pandas as pd
import numpy as np
from services import model_client

models_bp = Blueprint('models', __name__, url_prefix='/models')


@models_bp.route('/')
def list_models():
    """List all available models."""
    models = model_client.get_models(force_refresh=True)
    return render_template('models.html', models=models)


@models_bp.route('/refresh')
def refresh_models():
    """Refresh the model list."""
    model_client.invalidate_cache()
    return redirect(url_for('models.list_models'))


@models_bp.route('/create', methods=['GET', 'POST'])
def create_model():
    """Create a new model."""
    if request.method == 'GET':
        return render_template('models_create.html')

    # Handle file upload
    if 'dataset' not in request.files:
        flash('No dataset file uploaded', 'error')
        return redirect(url_for('models.create_model'))

    file = request.files['dataset']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('models.create_model'))

    try:
        # Read the dataset
        filename = file.filename.lower()
        if filename.endswith('.csv'):
            # Try reading with different encodings
            try:
                df = pd.read_csv(file, encoding='utf-8')
            except UnicodeDecodeError:
                file.seek(0)
                try:
                    df = pd.read_csv(file, encoding='latin1')
                except:
                    file.seek(0)
                    df = pd.read_csv(file, encoding='cp1252')
        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file)
        elif filename.endswith('.json'):
            df = pd.read_json(file)
        else:
            flash('Unsupported file format. Use CSV, Excel, or JSON.', 'error')
            return redirect(url_for('models.create_model'))

        # Get form data
        text_column = request.form.get('text_column')
        label_column = request.form.get('label_column')
        model_name = request.form.get('model_name', 'spam_model')
        timesteps = int(request.form.get('timesteps', 50000))

        # Validate columns
        if text_column not in df.columns or label_column not in df.columns:
            flash('Selected columns not found in dataset', 'error')
            return redirect(url_for('models.create_model'))

        # Clean data
        df_clean = df[[text_column, label_column]].dropna()
        records = df_clean.to_dict('records')

        # Train model
        success, result = model_client.train_model(
            records, text_column, label_column, model_name, timesteps
        )

        if success:
            flash(f'Model "{model_name}" trained successfully! Accuracy: {result.get("accuracy", 0):.2%}', 'success')
            return redirect(url_for('models.list_models'))
        else:
            flash(f'Training failed: {result}', 'error')
            return redirect(url_for('models.create_model'))

    except Exception as e:
        flash(f'Error processing dataset: {str(e)}', 'error')
        return redirect(url_for('models.create_model'))


@models_bp.route('/preview-columns', methods=['POST'])
def preview_columns():
    """Preview dataset columns for AJAX requests."""
    if 'dataset' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['dataset']
    try:
        filename = file.filename.lower()
        if filename.endswith('.csv'):
            # Try reading with different encodings
            try:
                df = pd.read_csv(file, encoding='utf-8')
            except UnicodeDecodeError:
                file.seek(0)
                try:
                    df = pd.read_csv(file, encoding='latin1')
                except:
                    file.seek(0)
                    df = pd.read_csv(file, encoding='cp1252')
        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file)
        elif filename.endswith('.json'):
            df = pd.read_json(file)
        else:
            return jsonify({'error': 'Unsupported format'}), 400

        # Replace NaN and inf values with empty strings for JSON serialization
        preview_df = df.head(5).copy()
        # Replace inf values
        preview_df = preview_df.replace([np.inf, -np.inf], '')
        # Replace NaN values
        preview_df = preview_df.fillna('')
        preview_data = preview_df.to_dict('records')

        return jsonify({
            'columns': list(df.columns),
            'rows': len(df),
            'preview': preview_data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@models_bp.route('/<model_name>/delete', methods=['POST'])
def delete_model(model_name):
    """Delete a model."""
    success, message = model_client.delete_model(model_name)
    if success:
        flash(f'Model "{model_name}" deleted successfully', 'success')
    else:
        flash(f'Failed to delete model: {message}', 'error')
    return redirect(url_for('models.list_models'))


@models_bp.route('/<model_name>/finetune', methods=['GET', 'POST'])
def finetune_model(model_name):
    """Fine-tune an existing model."""
    if request.method == 'GET':
        metadata = model_client.get_model_metadata(model_name)
        return render_template('models_finetune.html', model_name=model_name, metadata=metadata)

    # Handle file upload for fine-tuning
    if 'dataset' not in request.files:
        flash('No dataset file uploaded', 'error')
        return redirect(url_for('models.finetune_model', model_name=model_name))

    file = request.files['dataset']
    try:
        filename = file.filename.lower()
        if filename.endswith('.csv'):
            # Try reading with different encodings
            try:
                df = pd.read_csv(file, encoding='utf-8')
            except UnicodeDecodeError:
                file.seek(0)
                try:
                    df = pd.read_csv(file, encoding='latin1')
                except:
                    file.seek(0)
                    df = pd.read_csv(file, encoding='cp1252')
        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file)
        elif filename.endswith('.json'):
            df = pd.read_json(file)
        else:
            flash('Unsupported file format', 'error')
            return redirect(url_for('models.finetune_model', model_name=model_name))

        text_column = request.form.get('text_column')
        label_column = request.form.get('label_column')
        timesteps = int(request.form.get('timesteps', 50000))
        new_model_name = f"{model_name}_finetuned"

        df_clean = df[[text_column, label_column]].dropna()
        records = df_clean.to_dict('records')

        success, result = model_client.train_model(
            records, text_column, label_column, new_model_name, timesteps
        )

        if success:
            flash(f'Model fine-tuned as "{new_model_name}"! Accuracy: {result.get("accuracy", 0):.2%}', 'success')
            return redirect(url_for('models.list_models'))
        else:
            flash(f'Fine-tuning failed: {result}', 'error')
            return redirect(url_for('models.finetune_model', model_name=model_name))

    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('models.finetune_model', model_name=model_name))


@models_bp.route('/api/list')
def api_list_models():
    """API endpoint to list models (for AJAX)."""
    models = model_client.get_models()
    return jsonify({'models': models})


@models_bp.route('/api/<model_name>/metadata')
def api_model_metadata(model_name):
    """API endpoint to get model metadata."""
    metadata = model_client.get_model_metadata(model_name)
    if metadata:
        return jsonify(metadata)
    return jsonify({'error': 'Model not found'}), 404

