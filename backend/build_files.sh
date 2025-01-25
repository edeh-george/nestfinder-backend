#build_files.sh
pip install requirements.txt
python3 manage.py collectstatic --noinput
