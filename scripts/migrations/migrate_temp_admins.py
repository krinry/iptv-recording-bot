import json
from datetime import datetime
from utils.database import get_database

def migrate_temp_admins():
    db = get_database()
    if db is None:
        print("Failed to connect to MongoDB. Exiting migration.")
        return

    temp_admins_collection = db["temp_admins"]

    try:
        with open("temp_admins.json", "r") as f:
            temp_admins_data = json.load(f)

        if temp_admins_data:
            # Convert string dates to datetime objects for better MongoDB handling
            # And prepare data for insertion
            admins_to_insert = []
            for user_id_str, expiry_date_str in temp_admins_data.items():
                try:
                    user_id = int(user_id_str)
                    expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d %H:%M:%S")
                    admins_to_insert.append({"user_id": user_id, "expiry_date": expiry_date})
                except ValueError as e:
                    print(f"Skipping invalid entry: {user_id_str}: {expiry_date_str} - {e}")
            
            if admins_to_insert:
                temp_admins_collection.insert_many(admins_to_insert)
                print(f"Migrated {len(admins_to_insert)} temporary admins to MongoDB.")
            else:
                print("No valid temporary admin data to migrate.")
        else:
            print("temp_admins.json is empty. No data to migrate.")

    except FileNotFoundError:
        print("temp_admins.json not found. No temporary admins to migrate.")
    except json.JSONDecodeError:
        print("Error decoding temp_admins.json. Check file format.")
    except Exception as e:
        print(f"An unexpected error occurred during migration: {e}")

if __name__ == "__main__":
    migrate_temp_admins()
