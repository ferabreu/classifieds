# CLASSIFIEDS
#### Video Demo:  <URL HERE>
#### Description:
*Classifieds* is a web application for managing classifieds listings, and display them as a board. It is being built it to replace an old APEX-based application used at the company I work for.

##### Development method and tooling
I decided to employ GitHub Copilot to generate the required code, based on my instructions. All the code and template files in this project contain a header acknowledging this. I perform manual corrections, but not in enough volume to justify commenting about them on the code.

I had no knowledge on how to use AI for anything, so I started learning by doing this project. Initially, I just "talked" with Copilot running "free" AI models, like GPT 4.1, and the code came up based on these interactions - it was instructive, but productivity was low. With time, I learned better ways to increase the code output and quality, by planning tasks around one or more specific enhancements or reorganizations (refactorings) I wanted to implement. Also, using paid, better models increased my productivity (tremendously).

I have some basic notions of agile development methodologies, so I started calling each development round a "sprint". Each sprint, in my process, is performed in a new branch in the project's repository, and composed by:

1) Planning:
   - Uses Copilot's "Plan" mode, and the "Auto" model.
   - Generates a plan prompt file.
2) Development:
   - Interactions are based on the items of the plan prompt:
     - the plan may be updated as needed.
   - Uses Copilot's "Agent" mode, with "Auto" or any specific model I find more suitable for the job at hand.
   - Generates the actual code, eventual documentation, and also updates that come up as required.
3) Review:
   - The generated code is reviewed against the plan.
   - Corrections are made.
   - The branch is merged to the main branch.
4) Leftovers:
   - I always find myself forgetting things. If these things are not "enough" for a new sprint, I add them to a "leftovers" branch.
   - Performed quickly, without prior formal planning.
   - Merged as soon as ready.

I always knew that knowing how to use Git is an essential skill for a good developer. Unfortunately, even during my time in college, when I took a Systems Analysis graduation course, I never fouond a teacher that would do more than "commit code to master" (back then, that was the name of the "main" branch of a repository). So, to learn how to better use Git, I decided to rely on GitHub's tooling to help me to create a method suitable for my needs. By reading the relevant documentation and with the help of Copilot, I learned to:

1) Use branches to create the functionality I want in an organized fashion.
2) Open pull requests:
   - With Copilot reviewing the code of the branch.
   - Making necessary corrections before merging the branch.
   - And even decide between different merge modes.
3) Put my ideas on "issues", and check them to come up with the plan for the next development sprint.

##### Design decisions
CS50x gave me the basis for good coding (learning to "model" a problem, avoid reinventing the wheel, writing code that is organized and mantainable) many years ago, on the first time I took the course - when you had to download a virtual machine to use the "CS50x environment". For personal reasons, I could not finish it at the time. I took several other programming courses over the years, and also learned to observe software while using it.

However, I am not an experienced developer. And, maybe because I relied on something I still don't fully understand, I took a bad design decision right at the beginning of the project: I decided that *Classifieds* would be a board of items organized by "types" and "categories". Soon, I figured that was not flexible enough for a good classifieds board. I asked Copilot about the problem, and they proposed a "self-referring categories" model, in which each category could have a "parent". I instantly recognized the "recursion" pattern I learned in CS50x, and decided to refactor the whole application and database to use this new model. At the time, however, I was not familiar with planning and "sprints", and still employed Copilot for direct code editing, using free models - so, I took a long time to finish the refactoring.

The other major refactoring was about separation of concerns based on entities. Initially, the app had routes for types, categories, listings, users, and "admin" (apart from other "general" ones, like error displaying and authorization control). However, with time, I realized it made more sense to separate the functions/routes not by "admin or non-admin", but by entity - and the entities are listings, users, and categories. So, all the administrative functions were moved from the admin routing file to the entities routing files - except the route for displaying the administration dashboard, that remained in the admin.py file.


##### Application details/structure/workings
*Classifieds* is based on the following components:

- Python 3.10+: programming language.
- Flask: web framework.
- Flask-SQLAlchemy: ORM (database access).
- SQLite3: database engine.
- Flask-Migrate: database migrations.
- Flask-Login: user authentication.
- WTForms: forms and validation.
- Pillow: image processing.
- Werkzeug: password hashing.
- Jinja: HTML templating (frontend).
- HTML/CSS (Bootstrap 5)/JS: frontend technologies.

At the beginning of the project, I included requirements considering the environment used by my company for running applications. These, however, were not properly developed so far. So, these components are included, but not actually used yet:

- python-ldap: LDAP authentication.
- Docker: containerization.
- Gunicorn: WSGI server.
- Apache: web server (used at the company I work for).

In it's current state, *Classifieds* is, like the APEX-based application it will replace, a simple board. It's not a selling or retailing platform. It does not have a shopping cart or a buy mechanism. What it does is this:

- Allow the user to:
  - Sign up and sign in.
  - Edit their profile.
    - A user has email, first and last name, and password.
  - Reset their password.
  - Create, edit and delete listings:
    - A listing has title, description, category, price, pictures, and owner.
- If the user is an administrator (there must always be one), they may also:
  - Create, edit and delete categories:
    - A category has name and, optionally, a parent category.
    - A category containing listings cannot be deleted.
  - Edit and delete users and listings of any user:
    - When a user is deleted, so are their listings.

Now, a description of the application workings/usage:
- The board displays cards containing listings names and a picture.
  - Cards are organized by categories.
  - Navigation is done through:
    - A left sidebar containing links to all the categories, hierarchically displayed, accessed by a hamburguer menu on the left of the navbar.
    - A breadcrumb line at the top of the listings board, below the nav bar.
- The nav bar contains links for:
  - Sign up, sign in, sign out.
  - User self-management tasks.
  - Administration management tasks.
  (OBS: these links also appear at the bottom of the left sidebar.)
- The administration pages allow managing:
  - Categories (create, edit, delete).
  - Listings (edit, delete).
  - Users (edit, delete).
  - There's also a very simple adminintration dashboard that, currently, contains only links for the actual administration pages.


The application is structured in an MVC architecture, with some very incipient API/AJAX endpoints. It encompasses the following files:

classifieds
├── app: the main app directory.
│   ├── cli: contains Flask CLI applications for auxiliary tasks (Python code).
│   │   ├── demo.py: generates demo listings with made-up information and images fetched from Unsplash.com.
│   │   └── maintenance.py: generates missing thumbnails for images.
│   ├── routes: contains the backend logic of the application (- )the "controllers" of the MVC architecture). These files are processed by the app server.
│   │   │       All Python code.
│   │   ├── admin.py: a single route for the administration dashboard.
│   │   ├── auth.py: logic for controlling user access and registration tasks, and session management.
│   │   ├── categories.py: all the logic that deals with category-related operations, including navigation on the site, and administrative tasks.
│   │   ├── decorators.py: contains "decorators" - Flask constructs for helping with authorization and permission to access routes/endpoints.
│   │   ├── errors.py: logic for generating error-pages for HTTP errors, displaying helper messages.
│   │   ├── listings.py: all the logic that deals with listing-related operations, and related administrative tasks.
│   │   ├── users.py: logic for user-related operations, and related administrative tasks.
│   │   └── utils.py: includes utility functions for image processing and category showcase generation.
│   ├── static: contains files related to the frontend. They are not processed by the app server, only "delivered" to the client and processed by it.
│   │   ├── css: contains Cascading Style Sheets files.
│   │   │   └── styles.css: overrides some of the styles of Bootstrap, and defines classes with custom styling for specific elements.
│   │   ├── img: contains images used by the interface.
│   │   │   ├── no-image.png: a generic placeholder image for listings with no images added. Not actually displayed, only base for a thumbnail.
│   │   │   └── no-image-thumbnail.png: a generic thumbnail, created from the generic placeholder image.
│   │   └── js: contains Javascript files. These are frontend related scripts, processed at the client, that add interactivity to some pages of the app.
│   │       ├── category_dropdowns.js: used by the listing form, to dynamically generate category-selection dropdown fields.
│   │       ├── checkbox_select_all.js: provides a "select all" functionality for forms with checkboxes.
│   │       │                           Allows the deletion of all items displayed on a form.
│   │       │                           Was used by the admin listing forms, before a decision to limit admin management powers.
│   │       │                           Not currently used. Kept in case it's needed in the future.
│   │       └── form_selection.js: handles the selection of radio buttons on the admin pages.
│   ├── templates: these files are rendered by the client browser to generate the application pages. They combine HTML code and Jinja placeholders.
│   │   │          These placeholders are processed as Python code, allowing "filling" the page with dynamic information provided by the backend.
│   │   ├── admin: templates for the administration management pages.
│   │   │          Except for the dashboard, they all operate in the same fashion, rendering a form with items for editing or deleting.
│   │   │   ├── admin_categories.html: page for categories management.
│   │   │   │                          Uses the macro file "category_list.html" to render categories in a hierarchical layout.
│   │   │   ├── admin_dashboard.html: the administration dashboard file, containing links for the other admin pages.
│   │   │   ├── admin_listings.html: page for listings management.
│   │   │   └── admin_users.html: page for users management.
│   │   ├── categories: templates for category-related pages.
│   │   │   └── category_form.html: the page that renders the form for creating and editing listings.
│   │   │                           Uses the "category_dropdowns.js" file to dynamically render dropdowns for parent-category selection.
│   │   ├── listings: templates for listing-related pages.
│   │   │   ├── listing_detail.html: the page that displays a listing, with all information and pictures.
│   │   │   └── listing_form.html: the page with the form for adding or editing a listing
│   │   ├── macros
│   │   │   ├── breadcrumb.html
│   │   │   ├── category.html
│   │   │   ├── category_list.html
│   │   │   ├── pagination.html
│   │   │   └── sidebar_category_tree.html
│   │   ├── users
│   │   │   ├── user_form.html
│   │   │   └── user_profile.html
│   │   ├── base.html
│   │   ├── error.html
│   │   ├── forgot_password.html
│   │   ├── index.html
│   │   ├── login.html
│   │   ├── register.html
│   │   └── reset_password.html
│   ├── config.py
│   ├── forms.py
│   ├── __init__.py
│   ├── ldap_auth.py
│   └── models.py
├── docs
├── instance
│   └── classifieds.db
├── migrations
│   ├── versions
│   │   ├── 04ede7750476_renamed_item_to_listing.py
│   │   ├── 48e4d4abe479_add_thumbnail_filename_to_listingimage.py
│   │   ├── 4f8a9b2c3d1e_add_url_name_to_category.py
│   │   ├── 7f2e1a3b9cde_merge_types_to_category.py
│   │   ├── a1b2c3d4e5f6_add_sort_order_to_category.py
│   │   ├── befe2371cacf_add_parent_id_to_category_for_.py
│   │   └── c2b7f4d1a9e0_add_index_on_category_url_name.py
│   ├── alembic.ini
│   ├── env.py
│   ├── README
│   └── script.py.mako
├── LICENSE
├── pyproject.toml
├── README.md
├── requirements-dev.txt
├── requirements.txt
└── wsgi.py
