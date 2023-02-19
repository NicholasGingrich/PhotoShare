To get setup to work on the app:

SQL:
1. To start: 'sudo /usr/local/mysql/support-files/mysql.server start' or 'brew services start mysql' (if installed from Homebrew)
2. Type 'mysql -u root -h 127.0.0.1 -p' and then press enter. This runs the mysql program specifying -u (user) as the root, -h (host) as your local computer (127.0.0.1 is a hostname of your local machine), and -p (password).

Flask: (make sure SQL is running)
1. python3 -m flask run
2. Open your favorite web browser, go to http://127.0.0.1:5000 

Git:
1. commit and push changes on seperate branches
2. git checkout main 
3. git merge (your branch) 
