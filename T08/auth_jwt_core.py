import os
from functools import wraps
from apiflask import APIFlask, Schema, abort
from apiflask.fields import Integer, String
from apiflask.validators import Length, Email
from flask_jwt_extended import create_access_token, jwt_required, JWTManager, get_jwt_identity, get_jwt
from werkzeug.security import generate_password_hash, check_password_hash

app = APIFlask(__name__, title="Python Auth")
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET", "key")
jwt = JWTManager(app)

db = {
    "users": {
        1: {"id": 1, "email": "admin@example.com", "username": "admin", "password": generate_password_hash("admin123"), "role": "admin"},
        2: {"id": 2, "email": "user@example.com", "username": "user", "password": generate_password_hash("user123"), "role": "user"},
    }
}
next_user_id = 3

class UserSchema(Schema):
    id = Integer(dump_only=True)
    email = String(required=True, validate=Email())
    username = String(required=True, validate=Length(min=3))
    role = String(dump_only=True) 

class SafeUserResponseSchema(Schema):
    id = Integer()
    email = String()
    username = String()
    role = String()

class LoginSchema(Schema):
    email = String(required=True, validate=Email())
    password = String(required=True)

class SignUpSchema(UserSchema):
    password = String(required=True, validate=Length(min=6), load_only=True)

class TokenSchema(Schema):
    token = String()

def admin_required():
    def wrapper(fn):
        @wraps(fn)
        @jwt_required()
        def decorator(*args, **kwargs):
            claims = get_jwt()
            if claims.get("role") != "admin":
                abort(403, "Forbidden: Admins only")
            return fn(*args, **kwargs)
        return decorator
    return wrapper

@app.post("/api/auth/login")
@app.input(LoginSchema)
@app.output(TokenSchema)
def login(json_data):
    email = json_data.get("email")
    password = json_data.get("password")

    user = next((u for u in db["users"].values() if u["email"] == email), None)

    if not user or not check_password_hash(user["password"], password):
        abort(401, "Invalid email or password.")
    
    additional_claims = {"role": user["role"]}
    token = create_access_token(identity=user["id"], additional_claims=additional_claims)
    return {"token": token}

@app.post("/api/auth/logout")
@jwt_required()
def logout():
    return {"message": "Successfully logged out. Please delete your token."}


@app.post("/api/users")
@app.input(SignUpSchema)
@app.output(SafeUserResponseSchema, status_code=201)
def create_user(json_data):
    global next_user_id
    email = json_data.get("email")
    username = json_data.get("username")

    if any(u["email"] == email for u in db["users"].values()):
        abort(409, "A user with this email already exists.")
    if any(u["username"] == username for u in db["users"].values()):
        abort(409, "A user with this username already exists.")

    new_user = {
        "id": next_user_id,
        "email": email,
        "username": username,
        "password": generate_password_hash(json_data["password"]),
        "role": "user"
    }
    db["users"][next_user_id] = new_user
    next_user_id += 1
    return new_user


@app.get("/api/users/me")
@app.output(SafeUserResponseSchema)
@jwt_required()
def get_current_user():
    current_user_id = get_jwt_identity()
    user = db["users"].get(current_user_id)
    if not user:
        abort(404, "User not found.")
    return user

@app.get("/api/users")
@app.output(SafeUserResponseSchema(many=True))
@admin_required()
def get_all_users():
    return list(db["users"].values())

@app.get("/api/users/<int:user_id>")
@app.output(SafeUserResponseSchema)
@jwt_required()
def get_user_by_id(user_id: int):
    current_user_id = get_jwt_identity()
    current_user_role = get_jwt().get("role")

    if current_user_role != "admin" and current_user_id != user_id:
        abort(403, "Forbidden: You can only view your own profile.")
    
    user = db["users"].get(user_id)
    if not user:
        abort(404, "User not found.")
    return user

@app.delete("/api/users/<int:user_id>")
@jwt_required()
def delete_user(user_id: int):
    current_user_id = get_jwt_identity()
    current_user_role = get_jwt().get("role")

    if current_user_role != "admin" and current_user_id != user_id:
        abort(403, "Forbidden: You can only delete your own account.")

    if user_id not in db["users"]:
        abort(404, "User not found.")

    del db["users"][user_id]
    return {"message": f"User with ID {user_id} successfully deleted."}


if __name__ == '__main__':
    app.run(debug=True)