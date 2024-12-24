from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

DATABASE_URI = 'sqlite:///panchakanya.db'
engine = create_engine(DATABASE_URI, echo=False)
Base = declarative_base()
Session = sessionmaker(bind=engine)


# User Model
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)

    fullname = Column(String(100), nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(250), nullable=False)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<User(id={self.id}, fullname={self.fullname}, username={self.username}, email={self.email})>"


# Product Model
class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True, index=True)

    category = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    price_range = Column(String(50), nullable=False)
    comments = Column(Text, nullable=True)
    filename = Column(String(255), nullable=True)

    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user = relationship('User', backref='products')

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<Product(id={self.id}, name={self.name}, category={self.category}, price={self.price_range})>"


def init_db():
    """Create all tables in the database."""
    Base.metadata.create_all(bind=engine)
