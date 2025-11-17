import reflex as rx

config = rx.Config(
    app_name="reflex_frontend",
    frontend_port=12007,
    backend_port=12008,
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ],
    # Add custom CSS
    stylesheets=[
        "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap",
        "/styles.css",
    ],
    # Enable CORS for development
    cors_allowed_origins=["*"],
    # Production settings
    deploy_url="https://benchhub-plus.com",
)