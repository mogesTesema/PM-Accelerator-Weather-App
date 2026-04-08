# config/settings/admin.py

JAZZMIN_SETTINGS = {
    # title of the window (Will default to current_admin_site.site_title if absent or None)
    "site_title": "PM Accelerator Weather App",

    # Title on the login screen (19 chars max) (defaults to current_admin_site.site_header if absent or None)
    "site_header": "Weather Admin",

    # Title on the brand (19 chars max) (defaults to current_admin_site.site_header if absent or None)
    "site_brand": "Weather AI Platform",

    # Logo to use for your site, must be present in static files, used for brand on top left
    # "site_logo": "images/weather_logo.png",

    # CSS classes that are applied to the logo above
    "site_logo_classes": "img-circle",

    # Welcome text on the login screen
    "welcome_sign": "Welcome to the Weather Admin Dashboard",

    # Copyright on the footer
    "copyright": "Moges Tesema",

    # Field name on user model that contains avatar ImageField/URLField/Charfield or a callable that receives the user
    "user_avatar": None,

    ############
    # Top Menu #
    ############
    "topmenu_links": [
        {"name": "Home",  "url": "admin:index", "permissions": ["auth.view_user"]},
        {"model": "auth.User"},
        {"app": "weather"},
    ],

    #############
    # Side Menu #
    #############
    "show_sidebar": True,
    "navigation_expanded": True,
    
    # Hide these apps when generating side menu
    "hide_apps": [],
    "hide_models": [],

    # Custom icons for side menu apps/models. FontAwesome is included in Jazzmin out of the box
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "weather.WeatherForecast": "fas fa-cloud-sun-rain",
        "weather.Location": "fas fa-map-marker-alt",
        "weather.SearchHistory": "fas fa-history",
    },
    
    # Custom CSS file
    "custom_css": "css/admin_custom.css",
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-info",
    "accent": "accent-info",
    "navbar": "navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": False,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-info",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "lumen", # good fast theme as a base
    "dark_mode_theme": "darkly",
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}
