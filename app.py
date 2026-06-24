from flask import Flask, request, jsonify, render_template
import joblib
import pandas as pd
import numpy as np
import os

app = Flask(__name__)

# Cargar el pipeline del modelo entrenado
model_path = os.path.join(os.path.dirname(__file__), 'model.joblib')
try:
    model_pipeline = joblib.load(model_path)
    print("Modelo cargado exitosamente.")
except Exception as e:
    model_pipeline = None
    print(f"Error al cargar el modelo: {e}")

# Columnas esperadas por el preprocesador en orden exacto
EXPECTED_COLUMNS = [
    'job_title', 
    'experience_years', 
    'education_level', 
    'skills_count', 
    'industry', 
    'company_size', 
    'location', 
    'remote_work', 
    'certifications'
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    if model_pipeline is None:
        return jsonify({
            'success': False,
            'error': 'El modelo no está disponible en este momento.'
        }), 500
        
    try:
        data = request.get_json()
        
        # Validar y extraer campos
        input_data = {}
        for col in EXPECTED_COLUMNS:
            if col not in data:
                return jsonify({
                    'success': False,
                    'error': f'Falta el campo obligatorio: {col}'
                }), 400
            
            value = data[col]
            
            # Validar y convertir tipos
            if col in ['experience_years', 'skills_count', 'certifications']:
                try:
                    input_data[col] = float(value)
                    if input_data[col] < 0:
                        return jsonify({
                            'success': False,
                            'error': f'El campo {col} no puede ser negativo.'
                        }), 400
                except ValueError:
                    return jsonify({
                        'success': False,
                        'error': f'El campo {col} debe ser un valor numérico válido.'
                    }), 400
            else:
                input_data[col] = str(value)
                
        # Crear DataFrame de Pandas con una sola fila y las columnas en orden correcto
        input_df = pd.DataFrame([input_data], columns=EXPECTED_COLUMNS)
        
        # Generar predicción utilizando el pipeline completo
        prediction = model_pipeline.predict(input_df)[0]
        
        # Asegurarse de que el salario no sea negativo debido a fluctuaciones marginales de la regresión
        salary_pred = max(0.0, float(prediction))
        
        return jsonify({
            'success': True,
            'salary': round(salary_pred, 2)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Ocurrió un error al realizar la predicción: {str(e)}'
        }), 500

if __name__ == '__main__':
    # Ejecutar localmente en el puerto 5000
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
