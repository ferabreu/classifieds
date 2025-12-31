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

To me, knowing how to use Git is an essential skill for a good developer. Unfortunately, even during my time in college, when I took a Systems Analysis graduation course, I never found a teacher that would do more than "commit code to master" (back then, that was the name of the "main" branch of a repository). So, to learn how to better use Git, I decided to rely on GitHub's tooling to help me to create a method suitable for my needs. By reading the relevant documentation and with the help of Copilot, I learned to:

1) Develop software using Git repositories hosted in GitHub.
   - The actual development of **Classifieds** is being done at https://github.com/ferabreu/classifieds. The necessary files have been copied from the repository to this CS50x's workspace.
2) Use branches to create the functionality I want in an organized fashion.
3) Open pull requests and merge branches:
   - With Copilot reviewing the code of the branch.
   - Making necessary corrections before merging the branch.
   - And even decide between different merge modes.
4) Put my ideas on "issues", and check them to come up with the plan for the next development sprint.

##### Design decisions
CS50x gave me the basis for good coding (learning to "model" a problem, avoid reinventing the wheel, writing code that is organized and maintainable) many years ago, on the first time I took the course - when you had to download a virtual machine to use the "CS50x environment". For personal reasons, I could not finish it at the time. I took several other programming courses over the years, and also learned to observe software while using it.

However, I am not an experienced developer. And, maybe because I relied on something I still don't fully understand, I took a bad design decision right at the beginning of the project: I decided that *Classifieds* would be a board of items organized by "types" and "categories". Soon, I figured that was not flexible enough for a good classifieds board. I asked Copilot about the problem, and they proposed a "self-referring categories" model, in which each category could have a "parent". I instantly recognized the "recursion" pattern I learned in CS50x, and decided to refactor the whole application and database to use this new model. At the time, however, I was not familiar with planning and "sprints", and still employed Copilot for direct code editing, using free models - so, I took a long time to finish the refactoring.

The other major refactoring was about separation of concerns based on entities. Initially, the app had routes for types, categories, listings, users, and "admin" (apart from other "general" ones, like error displaying and authorization control). However, with time, I realized it made more sense to separate the functions/routes not by "admin or non-admin", but by entity - and the entities are listings, users, and categories. So, all the administrative functions were moved from the admin routing file to the entities routing files - except the route for displaying the administration dashboard, that remained in the admin.py file.

##### Components:
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

During development, the following additional components are being used:

- Alembic: database migration tool.
- Black and Isort: PEP 8-compliant code formatters

At the beginning of the project, I included requirements considering the environment used by my company for running applications. These, however, were not properly developed so far. So, these components are included, but not actually used yet:

- python-ldap: LDAP authentication.
- Docker: containerization.
- Gunicorn: WSGI server.
- Apache: web server (used at the company I work for).

##### Further descriptions
The application is structured in an MVC architecture, with some very incipient API/AJAX endpoints. In its current state, *Classifieds* is, like the APEX-based application it will replace, a simple board. It's not a selling or retailing platform. It does not have a shopping cart or a buy mechanism. What it does is this:

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

Description of the application workings/usage:

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
  - There's also a very simple administration dashboard that, currently, contains only links for the actual administration pages.

##### Database schema Details
alembic_version: Alembic migration tracking table for database versioning.

| Column | Type | Constraints |
|--------|------|-------------|
| `version_num` | VARCHAR(32) | PRIMARY KEY |

category: Hierarchical category system supporting parent-child relationships and URL-friendly naming.

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | INTEGER | PRIMARY KEY, auto-increment |
| `name` | VARCHAR(64) | NOT NULL, UNIQUE(name, parent_id) |
| `url_name` | VARCHAR(128) | NOT NULL, UNIQUE(url_name, parent_id), INDEXED |
| `parent_id` | INTEGER | FOREIGN KEY → category(id), nullable (top-level categories) |
| `sort_order` | INTEGER | NOT NULL (for UI ordering) |

**Indexes:**
- `ix_category_url_name` on `url_name`

**Notes:**
- Self-referencing for hierarchical structure
- Supports unlimited nesting depth
- Both `name` and `url_name` must be unique within their parent context

user: System users with support for local authentication and LDAP integration.

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | INTEGER | PRIMARY KEY, auto-increment |
| `email` | VARCHAR(120) | NOT NULL, UNIQUE |
| `password_hash` | VARCHAR(128) | nullable (for LDAP users) |
| `first_name` | VARCHAR(64) | NOT NULL |
| `last_name` | VARCHAR(64) | NOT NULL |
| `is_ldap_user` | BOOLEAN | nullable |
| `is_admin` | BOOLEAN | nullable |

**Notes:**
- Email is unique identifier
- LDAP users may not have password_hash
- Admin flag controls access to administrative features

listing: Classified listings with ownership and categorization.

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | INTEGER | PRIMARY KEY, auto-increment |
| `title` | VARCHAR(64) | NOT NULL |
| `description` | TEXT | NOT NULL |
| `price` | FLOAT | nullable |
| `user_id` | INTEGER | NOT NULL, FOREIGN KEY → user(id) |
| `category_id` | INTEGER | NOT NULL, FOREIGN KEY → category(id) |
| `created_at` | DATETIME | nullable |

**Notes:**
- Each listing belongs to one user (creator)
- Each listing belongs to one category
- Price is optional (for non-priced items)

listing_image: Images associated with listings, with automatic thumbnail management.

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | INTEGER | PRIMARY KEY, auto-increment |
| `filename` | VARCHAR(256) | NOT NULL |
| `thumbnail_filename` | VARCHAR(256) | nullable |
| `listing_id` | INTEGER | NOT NULL, FOREIGN KEY → listing(id) ON DELETE CASCADE |

**Notes:**
- Multiple images per listing supported
- Automatic thumbnail generation (224x224 JPEG)
- ON DELETE CASCADE ensures cleanup when listing is deleted
- Original and thumbnail filenames stored separately

Relationships

One-to-Many Relationships

1. **User → Listing**: One user can create many listings
2. **Category → Listing**: One category can contain many listings
3. **Listing → ListingImage**: One listing can have many images

Self-Referencing Relationship

- **Category → Category**: Categories can have parent categories (hierarchical structure)

Cascading Deletes

- **Listing deletion** → automatically deletes all associated ListingImages

Key Design Features

- **Hierarchical Categories**: Support for nested category structures (e.g., Electronics → Computers → Laptops)
- **URL-Safe Naming**: `url_name` field enables clean URL generation for category hierarchies
- **Flexible Authentication**: Support for both local (password) and LDAP authentication
- **Image Management**: Separate storage of original and thumbnail filenames
- **Atomic Deletion**: CASCADE delete ensures orphaned images are cleaned up automatically
- **SQLite Compatible**: Uses batch mode for all schema modifications (no ALTER COLUMN operations)

Indexes

| Table | Column | Purpose |
|-------|--------|---------|
| category | url_name | Fast URL-based category lookups |

Foreign Key Constraints

| Table | Column | References | Behavior |
|-------|--------|-----------|----------|
| category | parent_id | category(id) | No action (allows NULL) |
| listing | user_id | user(id) | Restrict |
| listing | category_id | category(id) | Restrict |
| listing_image | listing_id | listing(id) | CASCADE delete |

##### Directory structure - file names and descriptions
classifieds
├── app: the main app directory.
│   ├── cli: contains Flask CLI applications for auxiliary tasks (Python code).
│   │   ├── demo.py: generates demo listings with made-up information and images fetched from Unsplash.com.
│   │   └── maintenance.py: generates missing thumbnails for images.
│   ├── routes: contains the backend logic of the application (the "controllers" of the MVC architecture).
│   │   │       These files are processed by the app server. All Python code.
│   │   ├── admin.py: a single route for the administration dashboard.
│   │   ├── auth.py: logic for controlling user access and registration tasks, and session management.
│   │   ├── categories.py: all the logic that deals with category-related operations, including navigation
│   │   │                  on the site, and administrative tasks.
│   │   ├── decorators.py: contains "decorators" - Flask constructs for helping with authorization and
│   │   │                  permission to access routes/endpoints.
│   │   ├── errors.py: logic for generating error-pages for HTTP errors, displaying helper messages.
│   │   ├── listings.py: all the logic that deals with listing-related operations, and related administrative tasks.
│   │   ├── users.py: logic for user-related operations, and related administrative tasks.
│   │   └── utils.py: includes utility functions for image processing and category showcase generation.
│   ├── static: contains files related to the frontend. They are not processed by the app server, only
│   │   │       "delivered" to the client and processed by it.
│   │   ├── css: contains Cascading Style Sheets files.
│   │   │   └── styles.css: overrides some of the styles of Bootstrap, and defines classes with custom
│   │   │                   styling for specific elements.
│   │   ├── img: contains images used by the interface.
│   │   │   ├── no-image.png: a generic placeholder image for listings with no images added. Not actually
│   │   │   │                 displayed, only base for a thumbnail.
│   │   │   └── no-image-thumbnail.png: a generic thumbnail, created from the generic placeholder image.
│   │   └── js: contains Javascript files. These are frontend related scripts, processed at the client,
│   │       │   that add interactivity to some pages of the app.
│   │       ├── category_dropdowns.js: used by the listing form, to dynamically generate category-selection
│   │       │                          dropdown fields.
│   │       ├── checkbox_select_all.js: provides a "select all" functionality for forms with checkboxes.
│   │       │                           Allows the deletion of all items displayed on a form.
│   │       │                           Was used by the admin listing forms, before a decision to limit
│   │       │                           admin management powers.
│   │       │                           Not currently used. Kept in case it's needed in the future.
│   │       └── form_selection.js: handles the selection of radio buttons on the admin pages.
│   ├── templates: these files are rendered by the client browser to generate the application pages.
│   │   │          They form the "view" of the MVC. They combine HTML code and Jinja placeholders.
│   │   │          These placeholders are processed as Python code, allowing "filling" the page with
│   │   │          dynamic information provided by the backend.
│   │   ├── admin: templates for the administration management pages.
│   │   │   │      Except for the dashboard, they all operate in the same fashion, rendering a form
│   │   │   │      with items for editing or deleting.
│   │   │   ├── admin_categories.html: page for categories management.Uses the macro file "category_list.html"
│   │   │   │                          to render categories in a hierarchical layout.
│   │   │   ├── admin_dashboard.html: the administration dashboard file, containing links for the other admin pages.
│   │   │   ├── admin_listings.html: page for listings management.
│   │   │   └── admin_users.html: page for users management.
│   │   ├── categories: templates for category-related pages.
│   │   │   └── category_form.html: the page that renders the form for creating and editing listings.
│   │   │                           Uses the "category_dropdowns.js" file to dynamically render dropdowns
│   │   │                           for parent-category selection.
│   │   ├── listings: templates for listing-related pages.
│   │   │   ├── listing_detail.html: the page that displays a listing, with all information and pictures.
│   │   │   └── listing_form.html: the page with the form for adding or editing a listing.
│   │   ├── macros: Jinja macros act like functions. They can take arguments and generate text output.
│   │   │   │       Very useful for repetitive logic.
│   │   │   ├── breadcrumb.html: used by index.html to generate the breadcrumb navigation line at the
│   │   │   │                    top of the listings boards.
│   │   │   ├── category.html: used by admin_listings.html to render the "category" column, displaying
│   │   │   │                  the category path of the listing.
│   │   │   ├── category_list.html: used by admin_categories.html to generate the "category" column,
│   │   │   │                       hierarchically organized.
│   │   │   ├── pagination.html: used to distribute content across several "pages within a page", loading
│   │   │   │                    from the database ad needed.
│   │   │   └── sidebar_category_tree.html: used by index.html to generate the sidebar category list,
│   │   │                                   organized hierarchically.
│   │   ├── users: templates for user-related pages.
│   │   │   ├── user_form.html: the page that renders the form for user sign up, profile edit, and user edit by admin.
│   │   │   └── user_profile.html: displays the profile of the user (or the user information to an administrator).
│   │   ├── base.html: this is the base template for the whole application. It renders the navbar,
│   │   │              and the content area.
│   │   ├── error.html: this template renders pages for displaying HTTP errors.
│   │   ├── forgot_password.html: renders the form where the user informs their password and requires
│   │   │                         a password reset link.
│   │   ├── index.html: the index template fills the content area of the base template with listing cards,
│   │   │               generating the board. It also renders the left sidebar.
│   │   ├── login.html: the template for the user login/sign in form.
│   │   ├── register.html: the template that renders the user sign up form.
│   │   └── reset_password.html: the form to define a new password, accessed by a link received via email
│   │                            (or, in a development environment, by an alternative mechanism).
│   ├── config.py: this file defines the available settings for the application, using constants.
│   ├── forms.py: this files uses WTForms - a Python library for validation and rendering of forms in web applications.
│   ├── \__init__.py: this file is the "Flask app factory and initializator". It creates the instance of the application
│   │                through the create_app() function. It also contains and auxiliary function for logging,
│   │                and auxiliary cli commands for initializing a recently-deployed *Classifieds* application
│   │                (creating the database, the necessary directories, etc).
│   ├── ldap_auth.py: this file provides LDAP authentication, which the company I work for requires.
│   │                 This functionality is not complete, and needs further development.
│   └── models.py: defines the model of the application - the "M" of the MVC architecture.
│                  The model represents the problem to be solved. It defines the entities the application deals with.
│                  In more practical terms, in an application like this, it is the basis for the
│                  definition of the database schema.
│                  When supported by an Object Relational Mapper (ORM), like the SQLAlchemy used by *Classifieds*,
│                  it also contains all the relationships between the different entities of the application.
│                  As already explained, Classifieds entities are listings, categories and users. The model
│                  encompasses these, and the relationships that exist between them.
├── docs: miscellaneous documentation created during the development.
├── instance: in this application, the sole purpose of this directory is containing the database file.
│   └── classifieds.db: the SQLite3 database used by the application.
├── migrations: migrations are the alterations defined for the schema of the database. They represent,
│   │           in the database, the current model.  When development makes an alteration to the model,
│   │           adding or altering an entity or relationship, a migration file must be created and applied
│   │           to the database, as an SQL altering script.
│   ├── versions: each file is an alteration to the database schema. They are not ordered as they
│   │   │         were applied during development.
│   │   ├── 04ede7750476_renamed_item_to_listing.py: the 1st migration - renamed the generic "item" to "listing".
│   │   ├── 48e4d4abe479_add_thumbnail_filename_to_listingimage.py: the 2nd migration - when I decided
│   │   │                                                           that it was better to use thumbnails
│   │   │                                                           instead of resized images.
│   │   ├── 4f8a9b2c3d1e_add_url_name_to_category.py: this 6th migration was used to allow the application
│   │   │                                             to have "semantic" paths in URLs, instead of references
│   │   │                                             to categories IDs, paths became the names of the categories.
│   │   ├── 7f2e1a3b9cde_merge_types_to_category.py: the 4th migration, also related to the self-referring
│   │   │                                            categories refactoring.
│   │   ├── a1b2c3d4e5f6_add_sort_order_to_category.py: the 5th migration, also about the the self-referring
│   │   │                                               categories refactoring.
│   │   ├── befe2371cacf_add_parent_id_to_category_for_.py: the 3rd migration - performed during the major
│   │   │                                                   refactoring that removed "types" and implemented
│   │   │                                                   self-referring categories.
│   │   └── c2b7f4d1a9e0_add_index_on_category_url_name.py: the last migration so far - actually a kind of leftover.
│   │                                                       Copilot forgot to add the index to the proper previous
│   │                                                       migration immediately after altering the model,
│   │                                                       so it was patched here later.
│   ├── alembic.ini: not actually part of the application - used by Alembic.
│   ├── env.py: not actually part of the application - used by Alembic.
│   ├── README: not actually part of the application - included by Alembic.
│   └── script.py.mako: not actually part of the application - used by Alembic.
├── LICENSE: the (GNU GPL 2) license file for the project.
├── pyproject.toml: project dependencies.
├── README.md: this report.
├── requirements-dev.txt: project dependencies (for development only).
├── requirements.txt: project dependencies.
└── wsgi.py: this file works as the entry point for the application, creating an interface between
             the web server and Flask.
