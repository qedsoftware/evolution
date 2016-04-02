# Evolution

## Overall status: alpha
This piece of software went through some QA testing and seems stable.
There were no real contests hosted on this system yet.

## Goals

Simple, robust system to streamline the work of data scientists and machine learning specialists, by allowing them to easily verify their results in an objective, non-biased way.

Currently it is prepared for internal use, but we may open in to the public when gets more complete, polished and secure.

## Technologies

The most important ones are:
* Python3
* Django
* Sass
* PostgreSQL (it may work with other dbs, but postgres is the only supported)
* nginx (again, it may work with other web servers)
* Github-flavored Markdown (for writing descriptions, announcements etc.)

## Installation

## For developers

We want everyone to be on the same page. All the matters in this section are open to discussion and may change.

### Design philosophy

#### Leading thoughts

This system should stay small and focused. If our needs grow to big - split to into several libraries/services/apps.

Correctness over convenience.

If in doubt stick with simple.

Be honest in your code. If something is wrong it should look wrong. If the code feels unclean or you need to workaround something, leave a comment, make it obvious. And no abstraction is usually better than bad abstraction.

DRY is very important, but don't mistake coincidence for a rule. Separation of concerns is even more important.

If there is some part that doesn't belong to webapp - like scoring runner, keep it separate. And don't force Django dependency on it.

#### Design conventions

Thin models and thin views. Put the logic into separate classes and functions - focused on one task and if possible not touching the db. By default put them in ``models.py``, but if there is some clear category, put them in separate file.

Models themselves should be only used as data persistence object, don't put business logic into them. Models already have their responsibility - persistence objects. And it really helps with Separations of Concerns and Interface Segregation.

Neither models nor business logic should know anything about the views. Be really strict about it.

Views should only be an interface, the "adapter" from http to business logic. It should be easy to add a json or commandline interface. Views know about models, but keep coupling minimal. Coupling templates and views isn't a big problem, but avoid it if is not necessary.

#### Architecture

The base app handles the grading. It doesn't know about the contests, the web interface. The queueing, setting up and running scoring mechanism belongs there. The running and isolating of the scoring script is done by an external mechanism (run_scoring.py). This external mechanism is likely to grow a lot. We may want to factor the grading logic out of the web app in the future.

The scoring has the following layers:
1. ``./manage.py grading`` - a simple loop polling for jobs
2. ``./manage.py grading_attempt_safe`` - runs already created grading attempt, isolating possible failures, by running next layer in a separate process
3. ``./manage.py grading_attemt`` - actually runs the grading attempt, gets the grading params from the db and sets up the grading environment.
4. ``run_scoring.py`` - runs scoring scripts, trying to prevent it from using too much resources. It is not a proper isolation, just something to prevent stupid bugs from bringing down the whole system.

This system supports only a single contest type and it is the decision that allows it to stay simple. It is handles by the contests app. It handles all the contest-specific matters. Contests shouldn't care about the specifics of the grading, all of that should be handled by base.

### Code conventions

Prefer class-based views. They allow more declarative style and very handy mixing-in functionality.

Don't depend to much on admin interface. The usual administrative actions should be available from the normal interface. Admin should stay as simple direct data access mechanism for superadmins only.

Use comments sparingly, remember that they need to be kept up-to-date. Ideally all the code would be obvious by itself. If there is a need focus on "why" rather than "how".

TODOs in the code are generally welcome, with some restrictions:
* The goal of TODO is to inform the developers that the solution is far from ideal and to encourage them to fix it, rather than workaround it.
* Fixing the problem NOW is preferred to fixing it in the future. TODOs should be only used when just fixing it would be a major distraction or the developer isn't sure of how to approach it.
* Use TODOs only for code related issues. Use TODO if a solution is not clean enough, insecure or doesn't work well enough. Missing features should be tickets not TODOs.
* TODO should be reasonably concrete. No "refactor these project". "This class sucks, because of X" is ok. "Do X" is even better.
* TODOs should be added with the possibility in mind, that they may stay for a long time unfixed. If it is something of priority add a ticket (and maybe TODO for navigation).
* The developers must remember that TODO is only a suggestion, if they see a better way, they don't have to stick with TODO instructions.
* If reading the code feels like swimming in TODO sea, it is a sign that something is seriously wrong - refactor it now.

### Testing

Both white-box and black-box tests are welcome.

We want all views to have behavioral tests and it is primary way of testing.
But testing the business layer is also very useful - allows testing more reliably, more thoroughly and errors are much easier to debug.

Avoid writing "fragile" tests - broken with every change, even if the code still works correctly. The most important point here is to avoid hardcoding full html chunks. Use beutiful soup if you have to. And if you can avoid looking too much at the html at all.

### UX

Usable, simple, clean.

Hide the underlying complexity from the user. The contest system should give the user sense of simplicity and robustness.

Try to keep pages simple and focused on one thing, menus & hierarchies flat.

Most users expect something less minimalistic styling-wise. We probably should make it look more fancy and more "on purpose". We want to avoid reaction "oh, there's no css",
even though almost everything is styled.

Current idea is to add more icons and graphics, play a little with layout and typography. Other ideas very welcome.

For sure, we don't want to have here yet another Boostrap site.

Supporting strange resulutions and mobile devices is nice, it should be possible to use it this way, but it's not going to be very common. We don't have to think a lot about that.

### Technology choice

Be conservative.

It is really painful to have unsupported/badly designed dependencies. So add them with care. In particular avoid unpopular django apps - these tend to go outdated quickly. If possible try to abstract away dependencies that are used in many places, so that they can be painlessly replaced.
