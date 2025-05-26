from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64

app = Flask(__name__)

df_movies = pd.read_csv('IMDb_Top_1000.csv')
conn = sqlite3.connect('votaciones.db', check_same_thread=False)
df_votes = pd.read_sql("SELECT * FROM votaciones", conn)
df_merged = pd.merge(df_votes, df_movies, left_on='movie_title', right_on='Title')

def plot_to_img(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('ascii')
    buf.close()
    return img_base64

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/top_movies')
def top_movies():
    top_10 = df_merged.groupby('Title')['calificacion'].mean().sort_values(ascending=False).head(10)
    fig, ax = plt.subplots(figsize=(8,6))
    top_10.plot(kind='barh', color='skyblue', ax=ax)
    ax.set_xlabel('Promedio de calificación de usuario')
    ax.set_title('Top 10 películas según calificación de usuarios')
    ax.invert_yaxis()
    img = plot_to_img(fig)
    plt.close(fig)
    return render_template('top_movies.html', plot_img=img)


@app.route('/calificar', methods=['GET', 'POST'])
def calificar():
    conn = sqlite3.connect('votaciones.db')
    c = conn.cursor()

    if request.method == 'POST':
        pelicula = request.form['pelicula']
        calificacion = request.form['calificacion']
        usuario_id = +1 

        c.execute("INSERT INTO votaciones (usuario_id, movie_title, calificacion) VALUES (?, ?, ?)",
                  (usuario_id, pelicula, calificacion))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    # Para el formulario GET
    df = pd.read_csv('IMDb_Top_1000.csv')
    peliculas = sorted(df['Title'].unique())

    conn.close()
    return render_template('calificar.html', peliculas=peliculas)



@app.route('/scatter_plot')
def scatter_plot():
    fig, ax = plt.subplots(figsize=(8,6))
    sns.scatterplot(data=df_merged, x='calificacion', y='Rating', hue='usuario_id', palette='Set2', ax=ax)
    ax.set_title('Calificación de usuarios vs Rating IMDb')
    ax.set_xlabel('Calificación usuario')
    ax.set_ylabel('Rating IMDb')
    ax.grid(True)
    img = plot_to_img(fig)
    plt.close(fig)
    return render_template('scatter_plot.html', plot_img=img)

@app.route('/generos')
def generos():
    df_movies['Genre'] = df_movies['Genre'].astype(str)
    generos = df_movies['Genre'].str.split(',', expand=True)[0]
    top_generos = generos.value_counts().head(10)
    fig, ax = plt.subplots(figsize=(8,6))
    top_generos.plot(kind='bar', color='coral', ax=ax)
    ax.set_ylabel('Cantidad')
    ax.set_title('Películas por género (más comunes)')
    img = plot_to_img(fig)
    plt.close(fig)
    return render_template('generos.html', plot_img=img)

if __name__ == '__main__':
    app.run(debug=True)
