# Internationalization (i18n) Guidance

To prepare the application for multilingual support, consider the following steps:

## 1. Use Flask-Babel for i18n

- Install Flask-Babel:
  ```
  pip install Flask-Babel
  ```
- Initialize Babel in your application:
  ```python
  from flask_babel import Babel

  app = Flask(__name__)
  babel = Babel(app)
  app.config['BABEL_DEFAULT_LOCALE'] = 'en'
  app.config['BABEL_DEFAULT_TIMEZONE'] = 'UTC'
  ```

## 2. Mark Strings for Translation

- In Python:
  ```python
  from flask_babel import _
  flash(_("Your item has been created!"), "success")
  ```
- In templates:
  ```jinja
  {{ _("Welcome to Classifieds!") }}
  ```

## 3. Extract and Manage Translations

- Extract messages:
  ```
  pybabel extract -F babel.cfg -o messages.pot .
  ```
- Initialize a new language:
  ```
  pybabel init -i messages.pot -d translations -l pt_BR
  ```
- Update and compile translations:
  ```
  pybabel update -i messages.pot -d translations
  pybabel compile -d translations
  ```

## 4. Language Selection

- Babel can auto-detect user locale or you can offer a language switcher.
  ```python
  @babel.localeselector
  def get_locale():
      # Use user preference, browser, or default
      return request.accept_languages.best_match(['en', 'pt_BR'])
  ```

## 5. Dates, Times, and Numbers

- Use Babel’s formatting tools for locale-aware output:
  ```python
  from flask_babel import format_datetime
  format_datetime(datetime.utcnow())
  ```

## 6. UI and Content

- Wrap all user-facing strings in `_()` for translation.
- Translate static content (emails, error messages, etc.).
- Render form and validation messages via translation.


## References

- [Flask-Babel Documentation](https://pythonhosted.org/Flask-Babel/)
- [Babel User Guide](https://babel.pocoo.org/en/latest/user/index.html)
