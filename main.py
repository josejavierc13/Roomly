# This file is used to run the Roomly Web Platform.
from website import create_app
app = create_app()
if __name__ == '__main__':
    app.run(debug=True)
    