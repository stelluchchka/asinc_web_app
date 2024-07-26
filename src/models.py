from sqlalchemy import Integer, Column, ForeignKey, String, Numeric, Boolean
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'
    
    id = Column(Integer, primary_key=True)
    full_name = Column(String(50), nullable=False)
    email = Column(String(32), nullable=False, unique=True)
    password = Column(String(32), nullable=False)
    isAdmin = Column(Boolean, name='is_admin', default=False)
    
    # Связь с аккаунтами пользователя
    accounts = relationship("Account", back_populates="user")
    def info(self):
        return {"id": self.id, "email": self.email, "full_name": self.full_name}
    def full_info(self):
        return {"id": self.id, "email": self.email, "full_name": self.full_name, "accounts": [{"balance": acc.balance} for acc in self.accounts]}

class Account(Base):
    __tablename__ = 'account'
    
    id = Column(Integer, primary_key=True)
    balance = Column(Numeric)
    id_user = Column(Integer, ForeignKey('user.id', ondelete="CASCADE"))
    
    # Связь с пользователем
    user = relationship("User", back_populates="accounts")

    def info(self):
        return {"id": self.id, "balance": self.balance}

class Transaction(Base):
    __tablename__ = 'transaction'
    
    id = Column(String(50), primary_key=True)
    summ = Column(Numeric, nullable=False)