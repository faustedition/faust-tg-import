faust-tg-import
===============

Tools for importing the Faust edition data into TextGrid

Usage
-----

To generate the TextGrid objects, type

    cd generate-tg-objects
    python generate-tg-objects.py path-to-xml-dir path-to-output-dir

To import the files to the sandbox:

1. edit `config/config.xml`
2. run:

    java -jar /path/to/kolibri-cli-2.7.1-SNAPSHOT.jar -c config/config.xml
