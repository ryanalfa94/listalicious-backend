# models/user.py
# This file defines the User model used to represent application users.
# It structures user-related fields and provides a method to convert the user object into a MongoDB-compatible dictionary.


from datetime import datetime, timezone
from typing import Optional

# this class expects an email, password and an optional username
class User:
    def __init__(
        self,
        email: str
        , hashed_password: str,
        username: Optional[str] = None
        ):
        
        """
        Initialize a User object.

        Args:
            email (str): User's email address.
            hashed_password (str): Hashed password (never store raw passwords).
            username (Optional[str], optional): Optional username/nickname. Defaults to None.
        """
        
        self.email = email
        self.hashed_password = hashed_password
        self.username = username
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        

def to_dict(self):

    #Convert the User object to a dictionary for MongoDB insertion.
    return {
        "email": self.email,
        "hashed_password":self.hashed_password,
        "username": self.username,
        "created_at": self.created_at,
        "updated_at": self.updated_at,
    }   
        