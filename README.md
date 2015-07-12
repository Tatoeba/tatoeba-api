tatoeba2-django
---------------

This is a bridge project between the current website's schema and python/django.


  ## Experimental Api

  - Dependencies:
    - Make sure you have the python2.7, python-dev, and python-pip packages.
    - You should also have an instance of mysql running with tatoeba's schema and mysql headers (libmysqlclient-dev on debian) and xapian headers (libxapian-dev).
    - If you need any of the packages, use a sequence of commands like this to retrieve them:
    ```sh
    apt-get update
    apt-get install python-dev
    apt-get install python-pip
    etc.
    ```
  - Then get the python dependencies with:
    ```sh
    pip install -r requirements.txt
    ```

- Configuration:
  - Copy settings.py.template to settings.py in the same directory.
  - Change settings in settings.py if necessary (db connection settings).
  - If you need to run the test suite set MANAGE_DB to True in settings.py


- Running the test suite:
  - You can run the accompanying test suite using:
  ```sh
  py.test
  ```

  - Add to indices:
    Change the queryset filters in index_queryset() to get a smaller set
    during development then run:

  ```sh
  ./manage.py update_index tatoeba2.<model_name>
  ```

  or omit the last argument to index all models

  then to run the dev server to interact with the api:

  ```sh
  ./manage.py runserver
  ```

  it should appear on localhost:8000

  ```sh
  curl -s 127.0.0.1:8000/api/sentences_search/?sentence_text="what"&format=json
  ```
