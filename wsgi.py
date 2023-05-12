from shadow_clone_api.shadow_clone_api import app

if __name__ == '__main__':
    app.config.from_object('config.DevConfig')
    app.run(debug=False)