About tgext.sendmailservice
-------------------------

tgext.sendmailservice is a TurboGears2 extension

Installing
-------------------------------

tgext.sendmailservice can be installed from pypi::

    pip install tgext.sendmailservice

should just work for most of the users.

Enabling
-------------------------------

To enable tgext.sendmailservice put inside your application
``config/app_cfg.py`` the following::

    import tgext.sendmailservice
    tgext.sendmailservice.plugme(base_config)

or you can use ``tgext.pluggable`` when available::

    from tgext.pluggable import plug
    plug(base_config, 'tgext.sendmailservice')
