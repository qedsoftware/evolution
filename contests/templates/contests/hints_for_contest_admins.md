## Description and rules

You can use [Github-flavored markdown](https://github.com/adam-p/markdown-here/wiki/Markdown-Cheatsheet), the same you could use in the README on github. Of course we don't support issue references and other github-specific things.

Please use *Description* to explain the problem and to provide the links to data.

In *Rules* describe the rules of the contest, what competitors are allowed to do. Aspects like collaboration between teams or restictions on tools should be covered there.

## Writing Scoring Scripts

Of course the contestants' solutions won't score themselves - we need to define a way of determining how good a submission is.
To do that we have to write a *scoring script*.

Scoring script is just a simple, single-file python3 script that takes the submitted solution and the answer file and outputs the score for the submission. It just has to follow a few simple conventions.

### Security Warning

Currently, there is very little isolation for scoring scripts. It is possible to make a terrible mess from the script. Don't do anything crazy and be careful - user data cannot be trusted.

**Please, remember: you are responsible as the author to make it secure.**

### Hello, world!

The simplest scoring script looks like that:
```python
print('ACCEPTED') # means that the submission format is OK and we'll give it a score
print('42') # actual score
```

It doesn't look at the submission at all - it just gives score 42 to everything.

### Conventions summary

* The first commandline argument is a contestant's solution.
* The second commandline argument is the answer file.
* In the first line of input write `ACCEPTED` if the contestant's solution makes sense or `REJECTED` if it doesn't.
* If you ACCEPTED the solution write the score in the second line and an optional comment afterwards. This comment will be visible when the user can see their core.
* If you REJECTED the solution write the reason you rejected it. It is usually a good idea to include the location of the error. This information will be visible to the user immadietely.

### What is allowed in the script?

You generally shouldn't interact with the outside world. You should just open the solution and answer file, read it and write the result to stdout (optionally some logs to stderr).

In particular:

* Do **NOT** open any further files.
* Do **NOT** write to any files.
* Do **NOT** touch the network.
* Do **NOT** create new processes.
* Do **NOT** use exec, pickle or any other mechanism that isn't secure with untrusted data.

Avoid outputting too much data. All the logs and data are saved for your convenience, but this means that if you output too much, we'll run out of resources. How much exactly? Hundreds of kilobytes per grading shouldn't be a problem. Megabytes are acceptable in special circumstances.

### Scoring Scripts FAQ

#### What libraries are available?

Everything included in Python standard library. If something else could be useful, please tell us.
