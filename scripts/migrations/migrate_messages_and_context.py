import json
from utils.database import get_database

def migrate_messages_and_context():
    db = get_database()
    if db is None:
        print("Failed to connect to MongoDB. Exiting migration.")
        return

    # Migrate user_messages.json
    user_messages_collection = db["user_messages"]
    try:
        with open("user_messages.json", "r") as f:
            user_messages_data = json.load(f)
        
        if user_messages_data:
            messages_to_insert = []
            for msg_id_str, msg_data in user_messages_data.items():
                msg_data["_id"] = int(msg_id_str) # Use msg_id as _id
                messages_to_insert.append(msg_data)
            
            if messages_to_insert:
                user_messages_collection.insert_many(messages_to_insert)
                print(f"Migrated {len(messages_to_insert)} user messages to MongoDB.")
        else:
            print("user_messages.json is empty. No data to migrate.")

    except FileNotFoundError:
        print("user_messages.json not found. No user messages to migrate.")
    except json.JSONDecodeError:
        print("Error decoding user_messages.json. Check file format.")
    except Exception as e:
        print(f"An unexpected error occurred during user_messages migration: {e}")

    # Migrate message_context.json
    message_context_collection = db["message_context"]
    try:
        with open("message_context.json", "r") as f:
            message_context_data = json.load(f)
        
        if message_context_data:
            context_to_insert = []
            for msg_id_str, context_data in message_context_data.items():
                context_data["_id"] = int(msg_id_str) # Use msg_id as _id
                # Ensure user_id and chat_id are integers if they exist
                if 'user_id' in context_data: context_data['user_id'] = int(context_data['user_id'])
                if 'chat_id' in context_data: context_data['chat_id'] = int(context_data['chat_id'])
                if 'original_msg_id' in context_data: context_data['original_msg_id'] = int(context_data['original_msg_id'])
                # source_message_id can be string or int, keep as is or convert if always int
                context_to_insert.append(context_data)
            
            if context_to_insert:
                message_context_collection.insert_many(context_to_insert)
                print(f"Migrated {len(context_to_insert)} message contexts to MongoDB.")
        else:
            print("message_context.json is empty. No data to migrate.")

    except FileNotFoundError:
        print("message_context.json not found. No message contexts to migrate.")
    except json.JSONDecodeError:
        print("Error decoding message_context.json. Check file format.")
    except Exception as e:
        print(f"An unexpected error occurred during message_context migration: {e}")

if __name__ == "__main__":
    migrate_messages_and_context()
