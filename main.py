from app import create_app

app = create_app()
# Update
if __name__ == "__main__":
    app.run(port=8080, debug=True)
