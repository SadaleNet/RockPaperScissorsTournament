python3 rps.py || exit 1 #initialize the database, if it isn't available yet.
gunicorn -w 2 -b 0.0.0.0:80 rps:app --access-logfile /app/data/access.log --error-logfile /app/data/error.log
