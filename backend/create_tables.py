from backend.app.database import Base, engine
from backend.app.models.transaction import Transaction
from backend.app.models.stage2_access_token import Stage2AccessToken

Base.metadata.create_all(bind=engine)

print("Tables created successfully!")