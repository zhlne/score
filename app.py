from flask import Flask, request, render_template, redirect, url_for, jsonify
import pandas as pd

app = Flask(__name__)
data_df = None

def assign_grade(score):
    if score >= 85:
        return 'A'
    elif score >= 75:
        return 'B'
    elif score >= 65:
        return 'C'
    elif score >= 55:
        return 'D'
    else:
        return 'F'

@app.route('/', methods=['GET', 'POST'])
def upload():
    global data_df
    if request.method == 'POST':
        file = request.files['file']
        if file:
            df = pd.read_csv(file)

            if 'rank' in df.columns:
                del df['rank']

            df = df.sort_values(by="final_score", ascending=False).reset_index(drop=True)

            scores = df['final_score']
            threshold_rank = int(len(scores) * 0.4 + 0.5)
            threshold_score = scores.iloc[threshold_rank - 1]

            def linear_adjust(x):
                if x >= threshold_score:
                    return x
                ratio = 60 / threshold_score
                return min(round(x * ratio), 100)

            df['adjusted_score'] = df['final_score'].apply(linear_adjust)
            df['grade'] = df['adjusted_score'].apply(assign_grade)
            data_df = df
            return redirect(url_for('query', uploaded=1))
    return render_template('upload.html')

@app.route('/query', methods=['GET', 'POST'])
def query():
    global data_df
    result = None
    uploaded = request.args.get("uploaded") == "1"
    if data_df is None:
        return render_template('query.html', result=None, error="尚未上傳任何成績檔案", uploaded=False)

    if request.method == 'POST':
        student_id = request.form['student_id']
        result = data_df[data_df['id'].astype(str) == student_id]

    return render_template('query.html', result=result, error=None, uploaded=uploaded)

@app.route('/chart-data')
def chart_data():
    global data_df
    if data_df is None:
        return jsonify({})
    grade_counts = data_df['grade'].value_counts().sort_index()
    labels = [str(label) for label in grade_counts.index]
    values = [int(v) for v in grade_counts.values]
    return jsonify({"labels": labels, "data": values})

if __name__ == '__main__':
    app.run(debug=True)