from app import app

if __name__ == "__main__":
    # Ejecutar la aplicación Flask en modo desarrollo
    app.run(host="0.0.0.0", port=5000, debug=app.config.get("DEBUG", False))
