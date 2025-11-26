# mini-project
2. Create a Virtual Environment

This keeps the project dependencies isolated:

python -m venv venv


Activate it:

Windows (CMD or Git Bash):

venv\Scripts\activate


Mac/Linux:

source venv/bin/activate

📦 3. Install Dependencies

Make sure you’ve included a file named requirements.txt in your repo.
If not, you can create it from your environment using:

pip freeze > requirements.txt


Then your friend installs everything with:

pip install -r requirements.txt

⚙️ 4. Run Migrations

This sets up the project’s database structure:

python manage.py makemigrations
python manage.py migrate

NOT REQUIRED!!!! (👤 5. Create a Superuser (Optional)

Only needed if they want access to the Django admin panel:

python manage.py createsuperuser)!!


They’ll be prompted for a username, email, and password.

🚀 6. Run the Development Server

Start the project locally:

python manage.py runserver
