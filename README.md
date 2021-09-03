Depoverflow
-----------

This tool checks your source code for references to Stackoverflow answers and GitHub issues and warns you if those change.

Why?
----

There are plenty of tools that will let you know if your package dependencies have changed (`poetry show -o`, `npm outdated`, ...). There are even cloud-based services like Dependabot.

However, if you copy/paste code from Stackoverflow answers or GitHub issues, you will never be notified of updates.

Features
--------

* Find references to Stackoverflow answers and questions in code comments, to alert of edits and/or comments
* Find references to GitHub issues in code comments, to alert of open and close events and/or comments
* Optionally supports specific keywords such as "Works around"
* Saves current status of referenced items in a TOML file (similar to a lockfile), that you can check into version control (or not)
