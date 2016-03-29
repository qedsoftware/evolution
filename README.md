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

### Design philosophy

#### Leading thoughts

Correctness over convenience.

If in doubt stick with simple.

#### Architecture

TODO

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
