from sqlalchemy.ext.declarative import declarative_base
from zope.sqlalchemy import ZopeTransactionExtension
from sqlalchemy.orm import scoped_session, sessionmaker

DeclarativeBase = declarative_base()


maker = sessionmaker(autoflush=True, autocommit=False,
                     extension=ZopeTransactionExtension())

DBSession = scoped_session(maker)

metadata = DeclarativeBase.metadata


def init_model(engine1 ):
    """Call me before using any of the tables or classes in the model."""
    DBSession.configure(bind=engine1)
    metadata.bind = engine1
    

from surveymodel import SendMail