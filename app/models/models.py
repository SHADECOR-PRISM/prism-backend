import uuid
from sqlalchemy import Column, String, Boolean, Enum, Integer, ForeignKey, Date, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import relationship
from datetime import datetime

class Base(DeclarativeBase):
  pass

# --- Users Table ---
class Users(Base):
  __tablename__ = "users"

  # attribute
  id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  user_id = Column(String(8), unique=True, nullable=False)
  name = Column(String(255), nullable=False)
  role = Column(Enum('admin', 'general', name='user_role'), nullable=False)
  is_active = Column(Boolean, default=True)
  created_at = Column(DateTime(timezone=True))

  # relationship
  applications = relationship("ApplicationHeader", back_populates="applicant", foreign_keys="ApplicationHeader.user_id")
  approved_apps = relationship("ApplicationHeader", back_populates="approver", foreign_keys="ApplicationHeader.approved_by")

# --- Project Table ---
class Project(Base):
  __tablename__ = "projects"

  # attribute  
  id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  name = Column(String(255), nullable=False)
  total_budget = Column(Integer, default=0)
  is_active = Column(Boolean, default=True)
  created_at = Column(DateTime(timezone=True))
  
  # relationship
  headers = relationship("ApplicationHeader", back_populates="project")

# --- Application Header Table ---
class ApplicationHeader(Base):
  __tablename__ = "application_headers"
  
  # attribute
  id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
  project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
  approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
  
  type = Column(Enum('expense', 'income', name='application_type'), default='expense')
  applied_at = Column(DateTime, default=datetime.now)
  approved_at = Column(DateTime, nullable=True)
  status = Column(Enum('pending', 'approved', 'rejected', name='approval_status'), default='pending')
  total_amount = Column(Integer, default=0)
  created_at = Column(DateTime(timezone=True))
  
  # relationship
  applicant = relationship("Users", foreign_keys=[user_id], back_populates="applications")
  approver = relationship("Users", foreign_keys=[approved_by], back_populates="approved_apps")
  project = relationship("Project", back_populates="headers")
  
  transport_details = relationship("TransportationDetail", back_populates="header")
  expense_details = relationship("ExpenseDetail", back_populates="header")

# --- Transportation Detail Table ---
class TransportationDetail(Base):
  __tablename__ = "transportation_details"
  
  # attribute
  id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  header_id = Column(UUID(as_uuid=True), ForeignKey("application_headers.id"), nullable=False)
  usage_date = Column(Date, nullable=False)
  category = Column(Enum('train', 'bus', 'taxi', 'air', 'other', name='transportation_category'), nullable=False)
  departure = Column(String(100))
  arrival = Column(String(100))
  amount = Column(Integer, nullable=False)
  status = Column(Enum('pending', 'approved', 'rejected', name='approval_status'), default='pending')
  created_at = Column(DateTime(timezone=True))
  
  # relationship
  header = relationship("ApplicationHeader", back_populates="transport_details")

# --- Expense Detail Table ---
class ExpenseDetail(Base):
  __tablename__ = "expense_details"
  
  # attribute
  id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  header_id = Column(UUID(as_uuid=True), ForeignKey("application_headers.id"), nullable=False)
  usage_date = Column(Date, nullable=False)
  category = Column(Enum(
      'system_admin', 'supplies', 'software_license', 'rental', 
      'travel_expenses', 'food_beverage', 'service_fee', 'others', 
      name='expense_category'
  ), nullable=False)
  remark = Column(Text)
  amount = Column(Integer, nullable=False)
  status = Column(Enum('pending', 'approved', 'rejected', name='approval_status'), default='pending')
  created_at = Column(DateTime(timezone=True))
  
  # relationship
  header = relationship("ApplicationHeader", back_populates="expense_details")