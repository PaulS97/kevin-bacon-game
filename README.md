<p align="center">
  <h1>🎬 Six Degrees of Kevin Bacon</h1>
  <i>Six Degrees of Separation, reimagined as a multiplayer web app</i>
</p>

---

![Python](https://img.shields.io/badge/Python-3.10-blue)
![Flask](https://img.shields.io/badge/Flask-2.3-green)
![Postgres](https://img.shields.io/badge/PostgreSQL-✓-blue)
![Socket.IO](https://img.shields.io/badge/Socket.IO-realtime-yellowgreen)
![Deployment](https://img.shields.io/badge/Deployed-GCP-orange)

---

## 🚀 Features
- 🔑 Create an account, log in, or play as a guest  
- 🎮 Solo mode and **online 2-player mode** across devices  
- ⚡ Real-time updates via Flask-SocketIO  
- 📊 User dashboard with saved game history  
- 💡 Hint system that runs a shortest-path search weighted by a custom movie/actor popularity score  
- 🔄 Robust to browser refresh (games persist)  
- 🧩 Replayable game chains for post-game visualization  

---

## 🛠️ Tech Stack
- **Backend:** Python (Flask), Flask-SocketIO, SQLAlchemy  
- **Frontend:** HTML, CSS, JavaScript (Jinja2 templates)  
- **Database:** PostgreSQL  
- **Data Processing:** Pandas 
- **Deployment:** Google Cloud VM (Ubuntu 22.04), Gunicorn + Eventlet, Nginx, tmux  

---

## 🎥 Data Sources
- **Actors:** [TMDB People Images (HuggingFace)](https://huggingface.co/datasets/ashraq/tmdb-people-image)  
- **Movies:** [TMDB Movies Dataset (Kaggle)](https://www.kaggle.com/datasets/asaniczka/tmdb-movies-dataset-2023-930k-movies)  
- **IMDb:** [IMDb Datasets](https://datasets.imdbws.com/)  
  - `title.ratings`  
  - `title.principals`  

---

## 📂 Project Structure
```
├── server.py          # Main Flask app
├── templates/         # HTML templates (Jinja2)
├── static/            # Frontend assets
├── requirements.txt   # Python dependencies
├── .gitignore
```

