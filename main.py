from website import create_app
# This file serves as the entry point for running the Flask application.
app = create_app()
if __name__ == '__main__':
    app.run(debug=True)
    